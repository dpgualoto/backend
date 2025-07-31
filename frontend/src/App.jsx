import React from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import { Box, Menu, MenuButton, MenuList, MenuItem, Button } from '@chakra-ui/react';
import { ChevronDownIcon } from '@chakra-ui/icons';
import Home from './components/Home';
import Viaticos from './components/Viaticos';
import Cash from './components/Cash';
import LiquidacionTC from './components/LiquidacionTC';

function App() {
  return (
    <Router>
      <Box p={4}>
        <Menu>
          <MenuButton as={Button} rightIcon={<ChevronDownIcon />}>
            Menu
          </MenuButton>
          <MenuList>
            <MenuItem as={Link} to="/">Home</MenuItem>
            <MenuItem as={Link} to="/viaticos">Viaticos</MenuItem>
            <MenuItem as={Link} to="/cash">Cash</MenuItem>
            <MenuItem as={Link} to="/liquidaciontc">Liquidacion Tarjeta Crédito</MenuItem>
          </MenuList>
        </Menu>
      </Box>

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/viaticos" element={<Viaticos />} />
        <Route path="/cash" element={<Cash />} />
        <Route path="/liquidaciontc" element={<LiquidacionTC />} />
      </Routes>
    </Router>
  );
}

export default App;
