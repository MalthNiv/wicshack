import { BrowserRouter, Routes, Route } from "react-router-dom";
import RecordPlayer from "./components/RecordPlayer";
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
