import { redirect } from "next/navigation";

// Workflow Map was moved into the rivendell project scope.
// Old URL kept as a permanent redirect so existing bookmarks still resolve.
export default function LegacyWorkflowRedirect() {
  redirect("/projects/rivendell/workflow");
}
