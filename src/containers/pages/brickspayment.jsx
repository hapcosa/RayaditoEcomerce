import React, { useEffect } from 'react';
import { initMercadoPago } from '@mercadopago/sdk-react';
import { Payment } from '@mercadopago/sdk-react';
initMercadoPago('TEST-5616010b-48ef-4d59-80f7-b6ba0b21ce0a')
const PaymentBrick = ({data}) => {
  const initialization = {
    amount: data,
        /*
         "amount" es el monto total a pagar por todos los medios de pago con excepción 
         de la Cuenta de Mercado Pago y Cuotas sin tarjeta de crédito, las cuales tienen su valor de procesamiento determinado en el backend a través del "preferenceId". Debe ser un número entero.
        */
    preferenceId: "<PREFERENCE_ID>",
   };
   const customization = {
    paymentMethods: {
      creditCard: "all",
      debitCard: "all",
      mercadoPago: "all",
    },
   };
   const onSubmit = async (
    { selectedPaymentMethod, formData }
   ) => {
    // callback llamado al hacer clic en el botón enviar datos
    return new Promise((resolve, reject) => {
      fetch("/process_payment", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      })
        .then((response) => response.json())
        .then((response) => {
          // recibir el resultado del pago
          resolve();
        })
        .catch((error) => {
          // manejar la respuesta de error al intentar crear el pago
          reject();
        });
    });
   };
   const onError = async (error) => {
    // callback llamado para todos los casos de error de Brick
    console.log(error);
   };
   const onReady = async () => {
    /*
      Callback llamado cuando el Brick está listo.
      Aquí puede ocultar cargamentos de su sitio, por ejemplo.
    */
   };
  

  return (
    <>
      <Payment
    initialization={initialization}
    customization={customization}
    onSubmit={onSubmit}
    onReady={onReady}
    onError={onError}
  />
    </>
          
        
    )
};

export default PaymentBrick;
