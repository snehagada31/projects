// Clicking a tweet photo opens this — full-screen dark overlay with the
// image enlarged, same pattern as the reply modal (click outside or
// press the X to close). This is what X actually does when you tap a photo.
export default function ImageLightbox({ src, onClose }) {
  if (!src) return null;

  return (
    <div
      className="lightbox"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <button className="lightbox__close" aria-label="Close image" onClick={onClose}>
        ✕
      </button>
      <img className="lightbox__image" src={src} alt="" />
    </div>
  );
}
