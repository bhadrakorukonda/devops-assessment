import { useEffect, useState } from "react";
import { fetchHello } from "./api";

function App() {
  const [message, setMessage] = useState("");

  useEffect(() => {
    fetchHello().then((data) => setMessage(data.message));
  }, []);

  return (
    <div style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h1>Frontend Connected to Backend</h1>
      <p>{message}</p>
    </div>
  );
}

export default App;
