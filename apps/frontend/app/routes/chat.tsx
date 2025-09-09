import type { Route } from "./+types/chat";
import { ChatPage } from "../chat/ChatPage";

export function meta(_props: Route.MetaArgs) {
  return [
    { title: "Chat - Business Improvement Project Management" },
    { name: "description", content: "Chat with AI agents for project management" },
  ];
}

export default function ChatPageRoute() {
  return <ChatPage />;
}
