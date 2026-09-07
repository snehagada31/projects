import { useState } from "react";

// The modal doesn't know or care WHICH tweet it's replying to — that's
// entirely App.jsx's job (it passes down `replyingTo` and decides what
// to do with the submitted text via `onSubmit`). This keeps the modal
// itself simple and reusable.
export default function ReplyModal({ replyingTo, onClose, onSubmit }) {
  const [text, setText] = useState("");

  if (!replyingTo) return null; // nothing to reply to = don't render at all

  function handleSubmit(e) {
    e.preventDefault();
    const trimmed = text.trim();
    if (!trimmed) return;
    onSubmit(trimmed);
    setText("");
  }

  return (
    <div className="modal" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal-content">
        <button id="modal-close" aria-label="Close" onClick={onClose}>
          ✕
        </button>
        <p className="modal-replying-to">Replying to {replyingTo.handle}</p>
        <form onSubmit={handleSubmit}>
          <img
            className="avatar"
            src="https://api.dicebear.com/7.x/avataaars/svg?seed=you"
            alt=""
          />
          <label htmlFor="modal-reply-input" className="visually-hidden">
            Post your reply
          </label>
          <textarea
            id="modal-reply-input"
            placeholder="Post your reply"
            value={text}
            onChange={(e) => setText(e.target.value)}
            autoFocus
          />
          <button type="submit">Reply</button>
        </form>
      </div>
    </div>
  );
}
