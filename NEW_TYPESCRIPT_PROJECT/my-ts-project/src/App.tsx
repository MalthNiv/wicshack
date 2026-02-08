import { BrowserRouter, Routes, Route } from "react-router-dom";
import RecordPlayer from "./components/RecordPlayer";
import FloatingNotes from "./components/FloatingNotes";
import CursorGlow from "./components/CursorGlow";
import StockPage from "./pages/StockPage";
import "./styles/global.css";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={
            <main className="app">
              <CursorGlow />
              <FloatingNotes />
              <header className="hero">
                <h1>NOW YOU HEAR ME</h1>
                <p className="subtitle">
                  i hear it, i like it, i want it, i buy it
                </p>
              </header>

              <RecordPlayer />
            </main>
          }
        />
        <Route path="/stock/:symbol" element={<StockPage />} />
      </Routes>
    </BrowserRouter>
  );
}
