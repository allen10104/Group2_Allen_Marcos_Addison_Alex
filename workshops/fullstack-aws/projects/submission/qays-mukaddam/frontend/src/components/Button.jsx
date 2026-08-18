// A reusable button with two looks: "primary" (filled gradient, for main
// actions like Sign In/Post) and "secondary" (outlined, for lesser actions).
export default function Button({ children, onClick, type = 'button', variant = 'primary', disabled = false }) {
  // Styles shared by both variants: padding, rounded corners, disabled state.
  const baseStyles = 'px-4 py-2 rounded-lg font-medium transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed';

  // Primary: solid cyan-to-violet gradient background, dark text.
  // Secondary: just a subtle border, transparent background.
  const variantStyles = variant === 'primary'
    ? 'bg-gradient-to-r from-accent to-accent-2 text-black hover:opacity-90'
    : 'border border-white/20 text-gray-200 hover:bg-white/5';

  return (
    // type lets a form's submit button actually submit the form.
    // disabled is passed straight through so callers can block double-clicks.
    <button type={type} onClick={onClick} disabled={disabled} className={`${baseStyles} ${variantStyles}`}>
      {children}
    </button>
  );
}