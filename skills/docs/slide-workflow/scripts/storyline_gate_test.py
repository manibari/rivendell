import subprocess
import tempfile
import unittest


SCRIPTS = __file__.rsplit("/", 1)[0]
SELFCHECK = SCRIPTS + "/storyline-selfcheck.sh"
HOOK = SCRIPTS + "/storyline-gate-hook.sh"
TEMPLATE = SCRIPTS + "/../storyline-template-general.md"


class StorylineGateTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.story = self.temp.name + "/storyline.md"

    def write_story(self, genre="internal", audience="同事", action="決定下一步", status="draft", signed_by=None, body="## 結論\n內容\n"):
        lines = ["---", "genre: " + genre, "audience: " + audience,
                 "expected_action: " + action, "status: " + status]
        if signed_by is not None:
            lines.append("signed_by: " + signed_by)
        content = ("\n".join(lines) + "\n---\n\n" + body).encode()
        with open(self.story, "wb") as stream:
            stream.write(content)
        return content

    def selfcheck(self, sign=False):
        args = ["bash", SELFCHECK]
        if sign:
            args.append("--sign")
        args.append(self.story)
        return subprocess.run(args, capture_output=True, text=True)

    def hook(self, skip=False):
        payload = ('{"tool_name":"Write","tool_input":{"file_path":"'
                   + self.temp.name + '/deck.pptx"},"cwd":"' + self.temp.name + '"}')
        command = ["bash", HOOK]
        if skip:
            command = ["env", "SK_SKIP_STORYLINE_GATE=1"] + command
        return subprocess.run(command, input=payload, capture_output=True, text=True)

    def test_internal_check_does_not_edit(self):
        original = self.write_story()
        result = self.selfcheck()
        self.assertEqual(result.returncode, 0, result.stderr)
        with open(self.story, "rb") as stream:
            self.assertEqual(stream.read(), original)

    def test_sign_preserves_body_and_other_frontmatter(self):
        original = self.write_story(body="## 結論\n保留原文\n\n尾行")
        result = self.selfcheck(sign=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        with open(self.story, "rb") as stream:
            signed = stream.read()
        self.assertIn(b"status: signed-off\n", signed)
        self.assertIn(b"signed_by: self-check\n", signed)
        self.assertRegex(signed.decode(), r"signed_at: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}")
        self.assertEqual(signed.split(b"---\n", 2)[2], original.split(b"---\n", 2)[2])
        self.assertIn(b"audience: \xe5\x90\x8c\xe4\xba\x8b\n", signed)

    def test_presales_and_missing_genre_cannot_sign(self):
        for genre in ("presales", None):
            with self.subTest(genre=genre):
                original = self.write_story(genre=genre or "internal")
                if genre is None:
                    original = original.replace(b"genre: internal\n", b"")
                    with open(self.story, "wb") as stream:
                        stream.write(original)
                result = self.selfcheck(sign=True)
                self.assertEqual(result.returncode, 2)
                with open(self.story, "rb") as stream:
                    self.assertEqual(stream.read(), original)

    def test_missing_audience_fails(self):
        self.write_story(audience="")
        result = self.selfcheck()
        self.assertEqual(result.returncode, 1)
        self.assertIn("audience", result.stdout)

    def test_placeholder_fails(self):
        self.write_story(body="## 結論\n<在這裡寫>\n")
        self.assertEqual(self.selfcheck().returncode, 1)

    def test_general_template_fails(self):
        with open(TEMPLATE, "rb") as stream:
            content = stream.read()
        with open(self.story, "wb") as stream:
            stream.write(content)
        self.assertEqual(self.selfcheck().returncode, 1)

    def test_missing_file_or_frontmatter(self):
        self.assertEqual(self.selfcheck().returncode, 2)
        with open(self.story, "wb") as stream:
            stream.write(b"## Heading\n")
        self.assertEqual(self.selfcheck().returncode, 2)

    def test_invalid_genre(self):
        self.write_story(genre="unknown")
        result = self.selfcheck()
        self.assertEqual(result.returncode, 2)
        self.assertIn("unknown", result.stderr)
        self.assertIn("presales", result.stderr)

    def test_hook_allows_internal_selfcheck_signoff(self):
        self.write_story()
        self.assertEqual(self.selfcheck(sign=True).returncode, 0)
        self.assertEqual(self.hook().returncode, 0)

    def test_hook_blocks_presales_selfcheck_signoff(self):
        self.write_story(genre="presales", status="signed-off", signed_by="self-check")
        result = self.hook()
        self.assertEqual(result.returncode, 2)
        self.assertIn("自行簽核不算", result.stderr)

    def test_hook_blocks_missing_genre_selfcheck_signoff(self):
        content = self.write_story(status="signed-off", signed_by="self-check")
        with open(self.story, "wb") as stream:
            stream.write(content.replace(b"genre: internal\n", b""))
        self.assertEqual(self.hook().returncode, 2)

    def test_hook_allows_legacy_presales_signoff(self):
        self.write_story(genre="presales", status="signed-off")
        self.assertEqual(self.hook().returncode, 0)

    def test_hook_blocks_draft(self):
        self.write_story()
        self.assertEqual(self.hook().returncode, 2)

    def test_hook_skip_allows_draft(self):
        self.write_story()
        self.assertEqual(self.hook(skip=True).returncode, 0)


if __name__ == "__main__":
    unittest.main()
