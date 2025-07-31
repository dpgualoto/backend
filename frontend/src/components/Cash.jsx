import React, { useState } from 'react';
import {
  Box, Button, FormControl, FormLabel, Input,
  SimpleGrid, useToast, Spinner
} from '@chakra-ui/react';

function CashDownload() {
  const [dates, setDates] = useState({ desde: '', hasta: '' });
  const [isLoading, setIsLoading] = useState(false);
  const toast = useToast();

  const handleChange = (e) => {
    setDates({
      ...dates,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!dates.desde || !dates.hasta) {
      toast({
        title: "Error",
        description: "Por favor, seleccione ambas fechas.",
        status: "error",
        duration: 3000,
        isClosable: true,
        position: "top",
      });
      return;
    }

    setIsLoading(true);

    const formattedDates = {
      inicio: dates.desde,
      fin: dates.hasta
    };

    try {
      const response = await fetch('http://localhost:5000/api/procesar_cash', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formattedDates)
      });

      const contentType = response.headers.get("Content-Type");
      if (!response.ok) {
        if (contentType && contentType.includes("application/json")) {
          const errorData = await response.json();
          throw new Error(errorData.error || "Error desconocido");
        } else {
          throw new Error("Error al procesar la solicitud.");
        }
      }

      if (contentType.includes("text/plain")) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        


        toast({
          title: "Archivo descargado",
          description: "El archivo fue generado y descargado correctamente.",
          status: "success",
          duration: 3000,
          isClosable: true,
          position: "top",
        });
      } else {
        throw new Error("El servidor no devolvió un archivo válido.");
      }

    } catch (error) {
      console.error("Error al descargar:", error);
      toast({
        title: "Error",
        description: error.message,
        status: "error",
        duration: 3000,
        isClosable: true,
        position: "top",
      });
    } finally {
      setIsLoading(false);
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
      <SimpleGrid columns={1} spacing={4}>
        <FormControl id="desde" isRequired>
          <FormLabel>Desde</FormLabel>
          <Input
            type="date"
            name="desde"
            value={dates.desde}
            onChange={handleChange}
          />
        </FormControl>

        <FormControl id="hasta" isRequired>
          <FormLabel>Hasta</FormLabel>
          <Input
            type="date"
            name="hasta"
            value={dates.hasta}
            onChange={handleChange}
          />
        </FormControl>
      </SimpleGrid>

      <Button
        mt={6}
        colorScheme="blue"
        type="submit"
        width="full"
        isLoading={isLoading}
        spinner={<Spinner size="sm" />}
      >
        Descargar archivo
      </Button>
    </Box>
  );
}

export default CashDownload;
