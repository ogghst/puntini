import type { Route } from "./+types/dashboard";
import { Dashboard } from "../components/dashboard/Dashboard";

export function meta(_props: Route.MetaArgs) {
  return [
    { title: "Dashboard - Business Improvement Project Management" },
    { name: "description", content: "Manage your business improvement projects with AI agents" },
  ];
}

export default function DashboardPage() {
  return <Dashboard />;
}
