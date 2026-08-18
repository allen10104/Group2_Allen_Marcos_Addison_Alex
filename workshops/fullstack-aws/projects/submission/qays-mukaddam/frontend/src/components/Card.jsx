// A reusable glass-panel container. Applies the .glass-card style defined
// in index.css, plus padding. className lets callers add extra spacing/
// sizing without duplicating the base look every time.
export default function Card({ children, className = '' }) {
  return (
    // glass-card is our custom class from index.css (translucent, blurred).
    // p-6 adds consistent internal padding on every card.
    <div className={`glass-card p-6 ${className}`}>
      {children}
    </div>
  );
}