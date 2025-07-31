import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Input,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  IconButton,
  SimpleGrid,
  HStack,
  useToast,
  Flex,
  Spacer,
} from '@chakra-ui/react';
import { AddIcon, DeleteIcon } from '@chakra-ui/icons';

function Viaticos() {
  const [formData, setFormData] = useState({
    fecha_emision: '',
    numero_factura: '',
    valor: 0,
    ruc: '',
    clave_acceso: '',
    establecimiento: '',
    punto_emision: '',
    codigo_cliente: '' // Nuevo campo para el código del cliente
  });

  const [detalles, setDetalles] = useState([{
    codigo_principal: '',
    cantidad: 0,
    precio_unitario: 0,
    precio_total_sin_impuesto: 0,
    codigo_porcentaje: ''
  }]);

  const toast = useToast();

  // Función para calcular el valor total automáticamente
  useEffect(() => {
    const total = detalles.reduce((acc, detalle) => acc + parseFloat(detalle.precio_total_sin_impuesto || 0), 0);
    setFormData((prevData) => ({
      ...prevData,
      valor: total.toFixed(2)
    }));
  }, [detalles]);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleDetalleChange = (index, e) => {
    const newDetalles = [...detalles];
    newDetalles[index][e.target.name] = e.target.value;
    setDetalles(newDetalles);
  };

  const addDetalle = () => {
    setDetalles([...detalles, {
      codigo_principal: '',
      cantidad: 0,
      precio_unitario: 0,
      precio_total_sin_impuesto: 0,
      codigo_porcentaje: ''
    }]);
  };

  const removeDetalle = (index) => {
    if (detalles.length > 1) {
      const newDetalles = detalles.filter((_, i) => i !== index);
      setDetalles(newDetalles);
    } else {
      toast({
        title: "Acción no permitida.",
        description: "Debe haber al menos una línea en los detalles.",
        status: "warning",
        duration: 3000,
        isClosable: true,
        position: "top",
      });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
  
    const invoiceData = {
      DocDate: formData.fecha_emision,
      CardCode: formData.codigo_cliente,
      NumAtCard: formData.numero_factura,
      U_HBT_SER_EST: formData.establecimiento,
      U_HBT_PTO_EST: formData.punto_emision,
      U_HBT_AUT_FAC: formData.clave_acceso,
      DocumentLines: detalles.map(detalle => ({
        Quantity: parseFloat(detalle.cantidad),
        SupplierCatNum: detalle.codigo_principal,
        LineTotal: parseFloat(detalle.precio_total_sin_impuesto)
      }))
    };
  
    try {
      const response = await fetch('http://localhost:5000/api/registrar_factura', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(invoiceData)
      });
  
      if (response.ok) {
        toast({
          title: "Factura registrada",
          description: "La factura se ha registrado exitosamente en SAP.",
          status: "success",
          duration: 3000,
          isClosable: true,
          position: "top",
        });
      } else {
        const errorData = await response.json();
        toast({
          title: "Error al registrar la factura",
          description: errorData.error || "Error desconocido.",
          status: "error",
          duration: 3000,
          isClosable: true,
          position: "top",
        });
      }
    } catch (error) {
      toast({
        title: "Error al conectar con el backend",
        description: "No se pudo conectar con el backend para registrar la factura.",
        status: "error",
        duration: 3000,
        isClosable: true,
        position: "top",
      });
    }
  };
  
  const fetchClienteData = async (ruc) => {
    try {
      const response = await fetch('http://localhost:5000/api/get_cliente', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ ruc })
      });
      const data = await response.json();

      if (response.ok) {
        setFormData((prevData) => ({
          ...prevData,
          codigo_cliente: data.CardCode
        }));
      } else {
        toast({
          title: "Error al obtener el cliente",
          description: data.error || "Error desconocido.",
          status: "error",
          duration: 3000,
          isClosable: true,
          position: "top",
        });
      }
    } catch (error) {
      toast({
        title: "Error al conectarse con la API",
        description: "Hubo un problema al intentar obtener el cliente.",
        status: "error",
        duration: 3000,
        isClosable: true,
        position: "top",
      });
    }
  };

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (file) {
      const formData = new FormData();
      formData.append('archivo_xml', file);

      try {
        const response = await fetch('http://localhost:5000/api/procesar_xml', {
          method: 'POST',
          body: formData,
        });
        const data = await response.json();

        if (response.ok) {
            const dateParts = data.viatico_data.fecha_emision.split('/');
            const formattedDate = `${dateParts[2]}-${dateParts[1].padStart(2, '0')}-${dateParts[0].padStart(2, '0')}`;

          setFormData((prevData) => ({
            ...prevData,
            ...data.viatico_data,
            fecha_emision: formattedDate,
          }));
          setDetalles(data.detalles);

          // Llamada para obtener el código del cliente usando el RUC
          fetchClienteData(data.viatico_data.ruc);

          toast({
            title: "XML procesado exitosamente",
            description: "Los datos del archivo XML se han cargado en el formulario.",
            status: "success",
            duration: 3000,
            isClosable: true,
            position: "top",
          });
        } else {
          toast({
            title: "Error al procesar el XML (Backend)",
            description: data.error || "Error desconocido.",
            status: "error",
            duration: 3000,
            isClosable: true,
            position: "top",
          });
        }
      } catch (error) {
        toast({
          title: "Error al procesar el XML (Frontend)",
          description: "Hubo un problema al intentar cargar el archivo.",
          status: "error",
          duration: 3000,
          isClosable: true,
          position: "top",
        });
      }
    }
  };

  return (
    <Box as="form" onSubmit={handleSubmit} p={6} boxShadow="md" bg="white">
      <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
        <FormControl id="fecha_emision" isRequired>
          <FormLabel>Fecha de Emisión</FormLabel>
          <Input type="date" name="fecha_emision" value={formData.fecha_emision} onChange={handleChange} size="sm" />
        </FormControl>

        <FormControl id="numero_factura" isRequired>
          <FormLabel>Número de Factura</FormLabel>
          <Input type="text" name="numero_factura" value={formData.numero_factura} onChange={handleChange} size="sm" />
        </FormControl>

        <FormControl id="ruc" isRequired>
          <FormLabel>RUC</FormLabel>
          <Input type="text" name="ruc" value={formData.ruc} onChange={handleChange} size="sm" />
        </FormControl>

        <FormControl id="clave_acceso" isRequired>
          <FormLabel>Clave de Acceso</FormLabel>
          <Input type="text" name="clave_acceso" value={formData.clave_acceso} onChange={handleChange} size="sm" />
        </FormControl>

        <FormControl id="establecimiento" isRequired>
          <FormLabel>Establecimiento</FormLabel>
          <Input type="text" name="establecimiento" value={formData.establecimiento} onChange={handleChange} size="sm" />
        </FormControl>

        <FormControl id="punto_emision" isRequired>
          <FormLabel>Punto de Emisión</FormLabel>
          <Input type="text" name="punto_emision" value={formData.punto_emision} onChange={handleChange} size="sm" />
        </FormControl>

        <FormControl id="codigo_cliente">
          <FormLabel>Código de Proveedor</FormLabel>
          <Input type="text" name="codigo_cliente" value={formData.codigo_cliente} readOnly size="sm" />
        </FormControl>

        <FormControl id="archivo_xml" isRequired>
          <FormLabel>Cargar XML</FormLabel>
          <Input type="file" onChange={handleFileChange} size="sm" />
        </FormControl>
      </SimpleGrid>

      <Table variant="simple" mt={8} size="sm">
        <Thead>
          <Tr>
            <Th>Código Principal</Th>
            <Th>Cantidad</Th>
            <Th>Precio Unitario</Th>
            <Th>Precio Total Sin Impuesto</Th>
            <Th>Código Porcentaje</Th>
            <Th>Acciones</Th>
          </Tr>
        </Thead>
        <Tbody>
          {detalles.map((detalle, index) => (
            <Tr key={index}>
              <Td>
                <Input
                  type="text"
                  name="codigo_principal"
                  value={detalle.codigo_principal}
                  onChange={(e) => handleDetalleChange(index, e)}
                  size="sm"
                />
              </Td>
              <Td>
                <Input
                  type="number"
                  name="cantidad"
                  value={detalle.cantidad}
                  onChange={(e) => handleDetalleChange(index, e)}
                  size="sm"
                />
              </Td>
              <Td>
                <Input
                  type="number"
                  name="precio_unitario"
                  value={detalle.precio_unitario}
                  onChange={(e) => handleDetalleChange(index, e)}
                  size="sm"
                />
              </Td>
              <Td>
                <Input
                  type="number"
                  name="precio_total_sin_impuesto"
                  value={detalle.precio_total_sin_impuesto}
                  onChange={(e) => handleDetalleChange(index, e)}
                  size="sm"
                />
              </Td>
              <Td>
                <Input
                  type="text"
                  name="codigo_porcentaje"
                  value={detalle.codigo_porcentaje}
                  onChange={(e) => handleDetalleChange(index, e)}
                  size="sm"
                />
              </Td>
              <Td>
                <HStack spacing={2}>
                  <IconButton
                    icon={<AddIcon />}
                    colorScheme="teal"
                    onClick={addDetalle}
                    size="sm"
                  />
                  <IconButton
                    icon={<DeleteIcon />}
                    colorScheme="red"
                    onClick={() => removeDetalle(index)}
                    size="sm"
                  />
                </HStack>
              </Td>
            </Tr>
          ))}
        </Tbody>
      </Table>

      <Flex mt={4} align="center" direction={{ base: 'column', md: 'row' }}>
        <Spacer />
        <FormControl id="valor" w={{ base: "100%", md: "auto" }} mr={{ base: 0, md: 4 }}>
          <FormLabel>Total</FormLabel>
          <Input type="number" name="valor" value={formData.valor} isReadOnly size="sm" />
        </FormControl>
      </Flex>

      <Box mt={4} textAlign={{ base: "center", md: "left" }}>
        <Button colorScheme="blue" type="submit" size="sm">
          Registrar
        </Button>
      </Box>
    </Box>
  );
}

export default Viaticos;
