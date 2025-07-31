import React, { useState } from 'react';
import { Box, Button, FormControl, FormLabel, Input, useToast, Spinner, Center } from '@chakra-ui/react';

function LiquidacionTC() {
  const [file, setFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const toast = useToast();

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!file) {
      toast({
        title: "Error",
        description: "Por favor, seleccione un archivo Excel.",
        status: "error",
        duration: 3000,
        isClosable: true,
        position: "top",
      });
      return;
    }

    setIsLoading(true); // Mostrar el spinner de carga

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:5000/api/procesar_excel', {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        console.log("Procesado con éxito:", data);
        toast({
          title: "Procesado",
          description: "El archivo ha sido procesado exitosamente.",
          status: "success",
          duration: 3000,
          isClosable: true,
          position: "top",
        });
      } else {
        const errorData = await response.json();
        toast({
          title: "Error",
          description: errorData.error || "Error desconocido al procesar el archivo.",
          status: "error",
          duration: 3000,
          isClosable: true,
          position: "top",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Hubo un problema al conectarse con el servidor.",
        status: "error",
        duration: 3000,
        isClosable: true,
        position: "top",
      });
    } finally {
      setIsLoading(false); // Ocultar el spinner de carga
    }
  };

  return (
    <Box
      as="form"
      onSubmit={handleSubmit}
      maxW="md"
      mx="auto"
      mt={8}
      p={6}
      boxShadow="md"
      bg="white"
      borderRadius="md"
    >
      <FormControl id="file" isRequired>
  <FormLabel>Archivo Excel</FormLabel>
  <label htmlFor="fileInput" style={{ 
    display: 'inline-block', 
    padding: '6px 12px', 
    cursor: 'pointer', 
    backgroundColor: '#319795', 
    color: 'white', 
    borderRadius: '4px',
    fontSize: '14px',
    fontWeight: 'bold',
    textAlign: 'center'
  }}>
    Examinar...
  </label>
  <Input 
    id="fileInput"
    type="file" 
    name="file" 
    accept=".xlsx,.xls" 
    onChange={handleFileChange} 
    style={{ display: 'none' }} 
  />
  {file && <span style={{ marginLeft: '10px' }}>{file.name}</span>}
</FormControl>


      <Button
        mt={6}
        colorScheme="teal"
        type="submit"
        width="full"
        isDisabled={isLoading}
      >
        {isLoading ? 'Procesando...' : 'Procesar'}
      </Button>

      {isLoading && (
        <Center mt={4}>
          <Spinner size="xl" />
        </Center>
      )}
    </Box>
  );
}

export default LiquidacionTC;
