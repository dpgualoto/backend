import React from 'react';
import { Box, Text } from '@chakra-ui/react';

function Home() {
    return (
        <Box 
            display="flex" 
            justifyContent="center" 
            alignItems="center" 
            height="100vh" 
            bgGradient="linear(to-b, white, gray.100)"
        >
            <Text 
                fontSize="4xl" 
                fontWeight="bold" 
                color="red.500"  // Aquí aplicamos el color rojo sólido
                textAlign="center"
            >
                Heinsonthech
            </Text>
        </Box>
    );
}

export default Home;
