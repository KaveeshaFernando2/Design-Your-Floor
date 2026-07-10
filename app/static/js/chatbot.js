// Show/Hide chatbot window
document.getElementById("chatbot-button").onclick = function () {
    const win = document.getElementById("chatbot-window");
    win.style.display = win.style.display === "flex" ? "none" : "flex";
};

document.getElementById("chatbot-send").onclick = sendMessage;

document.getElementById("chatbot-input").addEventListener("keypress", function(e) {
    if (e.key === "Enter") sendMessage();
});

// Auto replies (you can add more)
function botReply(message) {
    message = message.toLowerCase();

    if (message.includes("hello") || message.includes("hi")) {
        return "Hello! How can I assist you today?";
    }
    if (message.includes("order")) {
        return "You can view your orders through your dashboard.";
    }
    if (message.includes("delivery")) {
        return "Delivery usually takes 2 to 3 business days.";
    }
    if (message.includes("contact")) {
        return "You can reach our support at support@example.com";
    }

    return "I'm here to help! Try asking about orders, delivery, or support.";
}

// Send message
function sendMessage() {
    const input = document.getElementById("chatbot-input");
    const msg = input.value.trim();
    if (!msg) return;

    addMessage(msg, "user");
    input.value = "";

    setTimeout(() => {
        const reply = botReply(msg);
        addMessage(reply, "bot");
    }, 500);
}

// Add message to chat window
function addMessage(text, sender) {
    const box = document.getElementById("chatbot-messages");
    const div = document.createElement("div");
    div.className = `message ${sender}`;
    div.innerText = text;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
}


