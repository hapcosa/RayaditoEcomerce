import React from "react";
import moment from 'moment/moment';
import {useNavigate} from "react-router-dom";
import {Button} from "@material-tailwind/react";
const TableOrders = ({orders, process_repayment_auth, reset}) => {
    const colorRow = (orderState) => {
        if (orderState === 'rechazado' | orderState === 'no procesado') {
            return "bg-red-200"
        } else if (orderState === 'enviado') {
            return "bg-green-200"
        } else if (orderState === 'procesado') {
            return "bg-blue-gray-200"
        }
    }

    const navigate = useNavigate();
    const handleRowClick = (order) => {
        if (order.transaction_id === null) {
            navigate(`/dashboard/payment/${
                order.id
            }`);
        } else {
            navigate(`/dashboard/payment/${
                order.transaction_id
            }`);
        }

    }



    return (
        <>
            <main className="w-full">
                <div className="">
                    <div className="">
                        {/* We've used 3xl here, but feel free to try other max-widths based on your needs */}
                        <div className="">
                            <div className=" w-full sm:px-6">
                                <div className="px-4 md:px-10 py-4 md:py-7 bg-gray-100 rounded-tl-lg rounded-tr-lg">
                                    <div className="sm:flex items-center justify-between">
                                        <p className="text-base sm:text-lg md:text-xl lg:text-2xl font-bold leading-normal text-gray-800">Tus pedidos</p>
                                    </div>
                                </div>
                                <div className="bg-white shadow px-4 md:px-10 pt-4 md:pt-7 pb-5 overflow-y-auto">
                                    <table className="w-full  whitespace-nowrap">
                                        <thead>
                                            <tr className="h-16 w-full text-sm leading-none text-gray-800">
                                                <th className="font-normal text-left pl-12">Pedido</th>
                                                <th className="font-normal text-left pl-12">Estado</th>
                                                <th className="font-normal text-left pl-12">Cantidad</th>
                                                <th className="font-normal text-left pl-20">Valor Total</th>
                                                <th className="font-normal text-left pl-20">Fecha</th>
                                                <th className="font-normal text-left pl-20">Envio</th>
                                            </tr>
                                        </thead>
                                        <tbody className=" w-full">
                                            {
                                            orders.map((order) => (
                                                <tr key={order.id} onClick={
                                                        () => handleRowClick(order)
                                                    }
                                                    className={
                                                        `${
                                                            colorRow(order.status)
                                                        } bg-blue-gray-100 h-20 text-sm leading-none text-gray-800  hover:bg-gray-100 border-b border-t border-gray-100`
                                                }>
                                                    <td className="pl-4 cursor-pointer">

                                                        <div className="flex items-center">
                                                            <div className="pl-4">
                                                                <p className="font-medium">
                                                                    {
                                                                    order.transaction_id ? '#' + order.transaction_id : '#transaccion no procesada'
                                                                }</p>

                                                            </div>
                                                        </div>

                                                    </td>

                                                    <td className="pl-10">

                                                        <p className="text-sm  font-medium leading-none text-gray-800">
                                                            {
                                                            order.status
                                                        }</p>


                                                    </td>
                                                    <td className="pl-12">

                                                        <p className="font-medium">
                                                            {
                                                            order.count
                                                        }
                                                            Piezas</p>

                                                    </td>
                                                    <td className="pl-20">

                                                        <p className="font-medium">${
                                                            order.amount
                                                        }</p>


                                                    </td>
                                                    <td className="pl-20">

                                                        <p className="font-medium">
                                                            {
                                                            order.date_issued.substr(0, 10).split("-").reverse().join("/")
                                                        }</p>
                                                        <p className="text-xs leading-3 text-gray-600 mt-2">
                                                            {
                                                            moment(order.date_issued).fromNow()
                                                        }</p>

                                                    </td>
                                                    <td className="pl-20">

                                                        <div className="flex items-center">
                                                            <img className="shadow-md w-8 h-8 rounded-full"
                                                                src={
                                                                    order.shipping.photo
                                                                }/>
                                                        </div>

                                                    </td>

                                                </tr>
                                            ))
                                        } </tbody>
                                    </table>
                                </div>
                            </div>

                        </div>
                    </div>
                </div>
            </main>
        </>
    );;
}

export default TableOrders;
