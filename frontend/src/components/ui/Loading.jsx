export default function Loading({ mensaje }) {
    return (
      <div className="loading">
        <div className="spinner" />
        <p>{mensaje}</p>
      </div>
    );
  }