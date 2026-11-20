import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { routerBasename } from "./lib/paths";
import { About, DataPage, Methodology } from "./pages/About";
import { Atlas } from "./pages/Atlas";

export default function App() {
  return (
    <BrowserRouter basename={routerBasename()}>
      <Routes>
        <Route path="/" element={<Atlas />} />
        <Route path="/about" element={<About />} />
        <Route path="/methodology" element={<Methodology />} />
        <Route path="/data" element={<DataPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
