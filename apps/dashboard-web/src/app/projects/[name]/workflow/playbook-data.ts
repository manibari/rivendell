// Display types for platform/capabilities/workflows/playbooks/*.json.

export type ChipCategory = "core" | "gstack" | "critical";

export interface Chip {
  key: string;
  category: ChipCategory;
}

export interface OptionalRow {
  label: string;
  chips: Chip[];
  /** Optional second label appearing inline after the first chip group. */
  secondLabel?: string;
  secondChips?: Chip[];
  inlineNote?: string;
}

export interface Step {
  num: string;
  action: string;
  detail?: string;
  chips?: Chip[];
  optionals?: OptionalRow[];
  hardGate?: string;
  inlineNote?: string;
}

export interface Branch {
  id: string;
  label: string;
  lead?: string;
  steps: Step[];
}

export interface MaintenanceRow {
  when: string;
  chips: Chip[];
  /** Sequence separator between chip groups, e.g. "→" */
  sequence?: { connector: "arrow" | "then"; chips: Chip[] }[];
}

export type WorkflowId = "ui" | "backend" | "slide" | "maintenance";

export interface Workflow {
  id: WorkflowId;
  label: string;
  heading: string;
  lead?: { text: string; tone?: "warn" | "info" };
  steps?: Step[];
  branches?: Branch[];
  maintenance?: MaintenanceRow[];
}

export interface SkillDetail {
  desc: string;
  trigger?: string;
  skip?: string;
}
