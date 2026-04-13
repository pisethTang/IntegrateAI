import type Action from "./Action";


type Message = {
    id: string;
    role: "user" | "assistant";
    content: string;
    actions?: Action[];
    isStreaming?: boolean;
};



// const exampleMessage: Message = {
//     id: "1",
//     role: "user",
//     content: "Hello, how are you?"
// };

export default Message;