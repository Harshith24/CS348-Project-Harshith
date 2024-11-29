import React from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import MainPage from './components/MainPage';
import AddBook from './components/AddBook';
import EditBook from './components/EditBook';
import DeleteBook from './components/DeleteBook';

function App() {
    return (
        <Router>
            <div>
                <h1>Library Management</h1>
                <Routes>
                    <Route path="/" element={<MainPage />} />
                    <Route path="/add" element={<AddBook />} />
                    <Route path="/edit" element={<EditBook />} />
                    <Route path="/delete" element={<DeleteBook />} />
                </Routes>
            </div>
        </Router>
    );
}

export default App;
