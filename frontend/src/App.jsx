// import { useState } from 'react'
// import reactLogo from './assets/react.svg'
// import viteLogo from '/vite.svg'
import './App.css'
import AIHomeSearch from './AIHomeSearch'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import PropertySearch from './PropertySearch';

function App() {
  // const [count, setCount] = useState(0)

  return (
    <Router>
      <Routes>
        <Route path="/" element={<AIHomeSearch />} />
        <Route path="/search" element={<PropertySearch />} />
      </Routes>
    </Router>
  )
}

export default App
