// sk-sensors: temperature, fan and power readings as one JSON object.
//
// Apple Silicon exposes these without root through two interfaces, the same
// ones exelban/stats reads:
//   - AppleSMC keys over IOKit: T* temperatures (flt, deg C), F* fans (RPM),
//     P* rails (flt, W; PSTR = system total).
//   - IOReport "Energy Model" counters: per-block energy, sampled twice and
//     divided by the interval to get CPU / GPU / ANE / DRAM watts.
//   - IOReport "CPU Core Performance States" and "GPU Performance States":
//     per-core (and whole-GPU) time spent in each DVFS state over the same
//     window, from which cores.py derives active % and frequency.
// Classification into CPU/GPU/... happens in sensors.py; this binary only
// reports raw keys so a new chip's key layout never needs a rebuild.
//
// Build: clang -O2 -framework IOKit -framework CoreFoundation -lIOReport \
//          -o sk-sensors sensors.c
// Usage: sk-sensors [-i interval_ms] [KEY ...]
//   -i   IOReport sample window, default 250 ms
//   KEY  read only these SMC keys. Walking all ~3500 keys costs about a
//        second, so callers enumerate once and pass the list afterwards.
#include <CoreFoundation/CoreFoundation.h>
#include <IOKit/IOKitLib.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

// ---- SMC -------------------------------------------------------------------

typedef struct { char major, minor, build, reserved; uint16_t release; } SMCVers;
typedef struct { uint16_t version, length; uint32_t cpu, gpu, mem; } SMCPLimit;
typedef struct { uint32_t size, type; char attributes; } SMCKeyInfo;
typedef struct {
  uint32_t key;
  SMCVers vers;
  SMCPLimit plimit;
  SMCKeyInfo info;
  char result, status, cmd;
  uint32_t data32;
  uint8_t bytes[32];
} SMCParam;

enum { CMD_READ_BYTES = 5, CMD_READ_INDEX = 8, CMD_READ_INFO = 9 };

static io_connect_t smc;

static uint32_t fourcc(const char *s) {
  return (uint32_t)s[0] << 24 | (uint32_t)s[1] << 16 | (uint32_t)s[2] << 8 | (uint32_t)s[3];
}

static void unfourcc(uint32_t v, char *out) {
  out[0] = v >> 24; out[1] = v >> 16; out[2] = v >> 8; out[3] = v; out[4] = 0;
}

static int smc_call(SMCParam *in, SMCParam *out) {
  size_t size = sizeof(SMCParam);
  kern_return_t kr = IOConnectCallStructMethod(smc, 2, in, sizeof(SMCParam), out, &size);
  return kr != KERN_SUCCESS || out->result != 0;
}

static int smc_read(uint32_t key, SMCKeyInfo *info, uint8_t *bytes) {
  SMCParam in = {0}, out = {0};
  in.key = key;
  in.cmd = CMD_READ_INFO;
  if (smc_call(&in, &out)) return -1;
  *info = out.info;
  memset(&in, 0, sizeof in);
  memset(&out, 0, sizeof out);
  in.key = key;
  in.info.size = info->size;
  in.cmd = CMD_READ_BYTES;
  if (smc_call(&in, &out)) return -1;
  memcpy(bytes, out.bytes, sizeof out.bytes);
  return 0;
}

// Numeric value of a key, NAN when unreadable or of a type we do not decode.
static double smc_value(const SMCKeyInfo *info, const uint8_t *b) {
  char type[5];
  unfourcc(info->type, type);
  if (!strcmp(type, "flt ") && info->size == 4) { float f; memcpy(&f, b, 4); return f; }
  if (!strcmp(type, "ui8 ")) return b[0];
  if (!strcmp(type, "ui16")) return b[0] << 8 | b[1];
  if (!strcmp(type, "fpe2")) return (b[0] << 8 | b[1]) / 4.0;
  return NAN;
}

static void emit_key(uint32_t key, int *first) {
  SMCKeyInfo info;
  uint8_t b[32];
  char name[5];
  unfourcc(key, name);
  if (name[0] != 'T' && name[0] != 'F' && name[0] != 'P') return;
  if (smc_read(key, &info, b)) return;
  double v = smc_value(&info, b);
  if (isnan(v) || isinf(v)) return;
  // Keys are four printable chars; escape anyway so a stray quote or
  // backslash can never break the JSON.
  printf("%s\"", *first ? "" : ",");
  for (int c = 0; c < 4; c++) {
    if (name[c] == '"' || name[c] == '\\') putchar('\\');
    putchar(name[c] >= 32 && name[c] < 127 ? name[c] : '?');
  }
  printf("\":%.3f", v);
  *first = 0;
}

static void emit_smc(char **keys, int nkeys) {
  io_service_t svc = IOServiceGetMatchingService(kIOMainPortDefault, IOServiceMatching("AppleSMC"));
  if (!svc || IOServiceOpen(svc, mach_task_self(), 0, &smc) != KERN_SUCCESS) {
    printf("\"smc\":{\"error\":\"cannot open AppleSMC\"}");
    return;
  }
  IOObjectRelease(svc);
  int first = 1;
  if (nkeys) {
    printf("\"smc\":{");
    for (int i = 0; i < nkeys; i++)
      if (strlen(keys[i]) == 4) emit_key(fourcc(keys[i]), &first);
    printf("}");
    IOServiceClose(smc);
    return;
  }
  SMCKeyInfo info;
  uint8_t b[32];
  if (smc_read(fourcc("#KEY"), &info, b)) {
    printf("\"smc\":{\"error\":\"cannot read key count\"}");
    return;
  }
  uint32_t count = (uint32_t)b[0] << 24 | b[1] << 16 | b[2] << 8 | b[3];
  printf("\"smc\":{");
  for (uint32_t i = 0; i < count; i++) {
    SMCParam in = {0}, out = {0};
    in.cmd = CMD_READ_INDEX;
    in.data32 = i;
    if (smc_call(&in, &out)) continue;
    emit_key(out.key, &first);
  }
  printf("}");
  IOServiceClose(smc);
}

// ---- IOReport energy -------------------------------------------------------

typedef struct IOReportSubscription *IOReportSubscriptionRef;
extern CFDictionaryRef IOReportCopyChannelsInGroup(CFStringRef, CFStringRef, uint64_t, uint64_t, uint64_t);
extern IOReportSubscriptionRef IOReportCreateSubscription(void *, CFMutableDictionaryRef, CFMutableDictionaryRef *, uint64_t, CFTypeRef);
extern CFDictionaryRef IOReportCreateSamples(IOReportSubscriptionRef, CFMutableDictionaryRef, CFTypeRef);
extern CFDictionaryRef IOReportCreateSamplesDelta(CFDictionaryRef, CFDictionaryRef, CFTypeRef);
extern int64_t IOReportSimpleGetIntegerValue(CFDictionaryRef, int32_t);
extern CFStringRef IOReportChannelGetChannelName(CFDictionaryRef);
extern CFStringRef IOReportChannelGetUnitLabel(CFDictionaryRef);
extern CFStringRef IOReportChannelGetGroup(CFDictionaryRef);
extern void IOReportMergeChannels(CFDictionaryRef, CFDictionaryRef, CFTypeRef);
extern int32_t IOReportStateGetCount(CFDictionaryRef);
extern CFStringRef IOReportStateGetNameForIndex(CFDictionaryRef, int32_t);
extern int64_t IOReportStateGetResidency(CFDictionaryRef, int32_t);

static void put_escaped(const char *s) {
  for (const char *c = s; *c; c++) {
    if (*c == '"' || *c == '\\') putchar('\\');
    putchar(*c >= 32 ? *c : '?');
  }
}

static int cstr(CFStringRef ref, char *out, size_t n) {
  out[0] = 0;
  return ref && CFStringGetCString(ref, out, n, kCFStringEncodingUTF8);
}

static double unit_to_joules(CFStringRef unit) {
  char u[16] = "";
  if (unit) CFStringGetCString(unit, u, sizeof u, kCFStringEncodingUTF8);
  if (!strcmp(u, "mJ")) return 1e-3;
  if (!strcmp(u, "uJ")) return 1e-6;
  if (!strcmp(u, "nJ")) return 1e-9;
  return 0;  // unknown unit: skip rather than report a wrong scale
}

// Residency per DVFS state, one object per channel: {"PCPU0":{"IDLE":n,...}}.
static void emit_residency(CFArrayRef items) {
  printf("\"residency\":{");
  int first = 1;
  for (CFIndex i = 0; items && i < CFArrayGetCount(items); i++) {
    CFDictionaryRef item = CFArrayGetValueAtIndex(items, i);
    char group[64], name[128];
    if (!cstr(IOReportChannelGetGroup(item), group, sizeof group) || !strcmp(group, "Energy Model")) continue;
    if (!cstr(IOReportChannelGetChannelName(item), name, sizeof name)) continue;
    printf("%s\"", first ? "" : ",");
    put_escaped(name);
    printf("\":{");
    int n = IOReportStateGetCount(item);
    for (int k = 0; k < n; k++) {
      char state[64];
      if (!cstr(IOReportStateGetNameForIndex(item, k), state, sizeof state)) continue;
      printf("%s\"", k ? "," : "");
      put_escaped(state);
      printf("\":%lld", (long long)IOReportStateGetResidency(item, k));
    }
    printf("}");
    first = 0;
  }
  printf("}");
}

static void emit_energy(int interval_ms) {
  CFDictionaryRef chans = IOReportCopyChannelsInGroup(CFSTR("Energy Model"), NULL, 0, 0, 0);
  if (!chans) {
    printf("\"energy\":{\"error\":\"no Energy Model channels\"}");
    return;
  }
  // Core / GPU DVFS residency rides the same subscription so every number in
  // one reading covers the same window. Missing groups just add nothing.
  CFDictionaryRef cpu = IOReportCopyChannelsInGroup(CFSTR("CPU Stats"), CFSTR("CPU Core Performance States"), 0, 0, 0);
  CFDictionaryRef gpu = IOReportCopyChannelsInGroup(CFSTR("GPU Stats"), CFSTR("GPU Performance States"), 0, 0, 0);
  if (cpu) { IOReportMergeChannels(chans, cpu, NULL); CFRelease(cpu); }
  if (gpu) { IOReportMergeChannels(chans, gpu, NULL); CFRelease(gpu); }
  CFMutableDictionaryRef mchans = CFDictionaryCreateMutableCopy(kCFAllocatorDefault, 0, chans);
  CFRelease(chans);
  CFMutableDictionaryRef subbed = NULL;
  IOReportSubscriptionRef sub = IOReportCreateSubscription(NULL, mchans, &subbed, 0, NULL);
  if (!sub) {
    printf("\"energy\":{\"error\":\"subscription failed\"}");
    CFRelease(mchans);
    return;
  }
  CFDictionaryRef a = IOReportCreateSamples(sub, mchans, NULL);
  usleep((useconds_t)interval_ms * 1000);
  CFDictionaryRef b = IOReportCreateSamples(sub, mchans, NULL);
  CFDictionaryRef delta = (a && b) ? IOReportCreateSamplesDelta(a, b, NULL) : NULL;
  printf("\"energy\":{\"interval_ms\":%d,\"watts\":{", interval_ms);
  CFArrayRef items = delta ? CFDictionaryGetValue(delta, CFSTR("IOReportChannels")) : NULL;
  int first = 1;
  for (CFIndex i = 0; items && i < CFArrayGetCount(items); i++) {
    CFDictionaryRef item = CFArrayGetValueAtIndex(items, i);
    char group[64], name[128];
    if (!cstr(IOReportChannelGetGroup(item), group, sizeof group) || strcmp(group, "Energy Model")) continue;
    double scale = unit_to_joules(IOReportChannelGetUnitLabel(item));
    if (!scale || !cstr(IOReportChannelGetChannelName(item), name, sizeof name)) continue;
    // Per-frequency-level (DTL) channels: hundreds of rows, no reader.
    if (strstr(name, "DTL")) continue;
    double watts = IOReportSimpleGetIntegerValue(item, 0) * scale / (interval_ms / 1000.0);
    printf("%s\"", first ? "" : ",");
    put_escaped(name);
    printf("\":%.4f", watts);
    first = 0;
  }
  printf("}},");
  emit_residency(items);
  if (delta) CFRelease(delta);
  if (a) CFRelease(a);
  if (b) CFRelease(b);
  CFRelease(mchans);
  if (subbed) CFRelease(subbed);
}

int main(int argc, char **argv) {
  int interval_ms = 250, first_key = 1;
  if (argc > 2 && !strcmp(argv[1], "-i")) {
    interval_ms = atoi(argv[2]);
    first_key = 3;
  }
  if (interval_ms < 50 || interval_ms > 5000) interval_ms = 250;
  printf("{");
  emit_smc(argv + first_key, argc - first_key);
  printf(",");
  emit_energy(interval_ms);
  printf("}\n");
  return 0;
}
