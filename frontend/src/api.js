export const fetchHello = async () => {
  try {
    const response = await fetch("/api/hello");
    return await response.json();
  } catch (error) {
    console.error("Error fetching backend:", error);
    return { message: "Error connecting to backend" };
  }
};
