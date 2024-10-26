import Layout from '../../hocs/layout/layout';
import { connect } from 'react-redux'
import {list_orders, get_order_detail} from '../../redux/action/orders'
import { get_shipping_option_id } from '../../redux/action/shipping';
import { useParams, Navigate } from 'react-router';
import { useEffect, useState } from 'react';

import { Link } from 'react-router-dom';
import { process_repayment_auth, reset } from '../../redux/action/payment';
import moment from 'moment/moment';
import OrderItem from '../../components/orders/orderItem';
import Shippingbox from '../../components/shipping/shippingbox';
import 'moment/locale/es'
import { BuildingStorefrontIcon, CreditCardIcon, UserIcon } from "@heroicons/react/24/outline";
import {  Bars3Icon } from "@heroicons/react/24/solid";
import { Button } from '@material-tailwind/react';

const OrdeDetail =({
    order,
    isAuthenticated,
    get_order_detail,
    process_repayment_auth,
    reset,
    url,
    loading,
    payment

})=>{
    const params = useParams()
    const transaction_id = params.transaction_id
    useEffect(() => {
      window.scrollTo(0, 0);
      get_order_detail(transaction_id)
  }, []);
  if(!isAuthenticated )
        return <Navigate to="/"/>
  const [show, setShow] = useState(false)
  const colorRow = (orderState) => {
    if (orderState==='rechazado' | orderState==='no procesado'){
        return "text-red-300"
    }else if(orderState==='enviado'){
        return "text-green-300"
    }else if(orderState==='procesado'){
        return "text-blue-gray-300"
    }else{
        return"text-red-300"
    }
}
const buy = (order) => async e => {
    e.preventDefault();
    if(!loading){
        process_repayment_auth(order.id);
    }
}
if(loading){
    reset()
}
if(payment){ 
    payment = false
    reset()
    window.location.href = url
}

  const showItems = () => {
    return(
        <>
            {
                order && order.order_items && 
                order.order_items !== null && 
                order.order_items !== undefined && 
                order.order_items.length !== 0 && 
                order.order_items.map((item)=>{
                    return (
                        <>
                        <div key={item.id}>
                            <OrderItem
                                item={item}
                            />
                        </div>
                        </>
                    );
                })
            }
        </>
    )
}   
    const DifFecha = (fech) => {
        moment.locale('es')
        return moment(fech).fromNow()
    }

    
    return (
        <>
        <Layout>
          <div>
          <div className="w-full h-full bg-gray-100">
              <div className="flex flex-no-wrap">
                    {/* Sidebar starts */}
                    <div className="absolute lg:relative w-64  shadow bg-gray-300 hidden lg:block">

                        <ul aria-orientation="vertical" className="ml-8 py-6">
                            <Link to="/dashboard" className=" pl-6 cursor-pointer  text-sm leading-3 tracking-normal pb-4 pt-5 text-gray-600 focus:text-gray-800 focus:outline-none">
                                <div className="flex items-center">
                                    <div>
                                        <UserIcon className="h-5 w-5"/>
                                    </div>
                                    <span className="ml-2">Perfil</span>
                                </div>
                            </Link>
                            <Link to="/dashboard/profile" className="pl-6 cursor-pointer text-gray-600 text-sm leading-3 tracking-normal mt-4 mb-4 py-2 hover:text-gray-800 focus:text-gray-800 focus:outline-none">
                                <div className="flex items-center">
                                    <BuildingStorefrontIcon className='h-5 w-5'/>
                                    <span className="ml-2">Direcciones</span>
                                </div>
                            </Link>
                            <Link to="/dashboard/payments" className="pl-6 cursor-pointer text-gray-600 text-sm leading-3 tracking-normal mb-4 py-2 hover:text-gray-800 focus:text-gray-800 focus:outline-none">
                                <div className="flex items-center">
                                    <CreditCardIcon className='h-5 w-5'/>
                                    <span className="ml-2">Tus pedidos</span>
                                </div>
                            </Link>

                        </ul>
                    </div>
                    {/*Mobile responsive sidebar*/}
                    <div className={show ? "w-full h-full  absolute z-40  transform  translate-x-0 " : "   w-full h-full absolute z-40  transform -translate-x-full"} id="mobile-nav">
                        <div className="bg-gray-800 opacity-50 absolute h-full w-full lg:hidden" onClick={() => setShow(!show)} />
                        <div className="absolute z-40 sm:relative h-full w-64 md:w-64  shadow pb-4 bg-gray-300 lg:hidden transition duration-150 ease-in-out ">
                            <div className="flex flex-col justify-between h-full w-full">
                                <div>
                                    <div className="flex items-center justify-between px-8">
                                    
                                        <div id="closeSideBar" className=" mt-2 flex items-center justify-center  ml-48" onClick={() => setShow(!show)}>
                                            <svg xmlns="http://www.w3.org/2000/svg" className="icon icon-tabler icon-tabler-x" width={20} height={20} viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor" fill="none" strokeLinecap="round" strokeLinejoin="round">
                                                <path stroke="none" d="M0 0h24v24H0z" />
                                                <line x1={18} y1={6} x2={6} y2={18} />
                                                <line x1={6} y1={6} x2={18} y2={18} />
                                            </svg>
                                        </div>
                                    </div>
                                    <ul aria-orientation="vertical" className="ml-8 py-6">
                                    <Link to="/dashboard" className=" pl-6 cursor-pointer  text-sm leading-3 tracking-normal pb-4 pt-5 text-gray-600 hover:text-gray-800 focus:text-gray-800 focus:outline-none">
                                        <div className="flex items-center">
                                            <div>
                                                <UserIcon className="h-5 w-5"/>
                                            </div>
                                            <span className="ml-2">Perfil</span>
                                        </div>
                                    </Link>
                                    <Link to="/dashboard/profile" className="pl-6 cursor-pointer text-gray-600 text-sm leading-3 tracking-normal mt-4 mb-4 py-2 hover:text-gray-800 focus:text-gray-800 focus:outline-none">
                                        <div className="flex items-center">
                                            <BuildingStorefrontIcon className='w-5 h-5'/>
                                            <span className="ml-2">Direcciones</span>
                                        </div>
                                    </Link>
                                    <Link to="/dashboard/payments" className="pl-6 cursor-pointer text-gray-600 text-sm leading-3 tracking-normal mb-4 py-2 hover:text-gray-800 focus:text-gray-800 focus:outline-none">
                                        <div className="flex items-center">
                                            <CreditCardIcon className='h-5 w-5'/>
                                            <span className="ml-2">Tus pedidos</span>
                                        </div>
                                    </Link>

                                    </ul>
                                </div>
                                <div className="w-full">
                                    

                                </div>
                            </div>
                        </div>
                    </div>
                    {/*Mobile responsive sidebar*/}
                    {/* Sidebar ends */}
                    <div className="w-full">
                        {/* Navigation starts */}
                        <div className="text-gray-600 mr-8 m-2 visible lg:hidden relative" onClick={() => setShow(!show)}>
                                {show ? (
                                    " "
                                ) : (
                                    <Bars3Icon className="h-5 w-5" />
                                )}
                            </div>
                        {/* Navigation ends */}
                        {/* Remove class [ h-64 ] when adding a card block */}
                        <div className="container mx-auto py-10  md:w-4/5 w-11/12 px-6">
                            {/* Remove class [ border-dashed border-2 border-gray-300 ] to remove dotted border */}
                            <div className="w-full h-full ">
                        <div className="">
                        <div className="">
                        <div className="flex flex-col justify-start item-start space-y-2  ">
                            <h1 className={`ml-3 mt-3 text-3xl lg:text-4xl font-semibold leading-7 lg:leading-9 ${colorRow(order && order.status)}`}>Orden #{order && order.transaction_id} - {order && order.status}</h1>
                            <time className="ml-5 text-gray-600">{order && order && order.date_issued.substr(0,10).split("-").reverse().join("/")} - {DifFecha(order && order.date_issued)}</time>
                        </div>
                        <div className="mt-10 flex flex-col xl:flex-row jusitfy-center items-stretch  w-full xl:space-x-8 space-y-4 md:space-y-6 xl:space-y-0">
                            <div className="flex flex-col justify-start items-start w-full space-y-4 lg:space-y-7 md:space-y-6 xl:space-y-8">
                                <div className="flex flex-col justify-start items-start bg-gray-50 px-4 py-4 md:py-6 md:p-6 xl:p-8 w-full">
                                    <p className="text-lg md:text-xl font-semibold leading-6 xl:leading-5 text-gray-800">Piezas adquiridas</p>
                                    {showItems()}
                                </div>
                                {order && order.status === 'no procesado'? <Button onClick={buy(order)} className='hidden xl:block ml-10 items-center w-9/12'>Pagar</Button>:""}
                                
                            </div>
                            <div className="bg-gray-50 w-full xl:w-96 flex justify-between items-center md:items-start px-4 py-6 md:p-6 xl:p-8 flex-col ">
                                <h3 className="text-xl font-semibold leading-5 text-gray-800">Datos de envio</h3>
                                <div className="flex  flex-col justify-start items-stretch h-full w-full ">
                                <Shippingbox shipping={order && order.shipping}/>
                                    <div className="flex flex-col justify-start items-start flex-shrink-0">
                                        <div className="flex justify-center  w-full  md:justify-start items-center space-x-4 py-8 border-b border-gray-200">
                                            
                                            <div className=" flex justify-start items-start flex-col space-y-2">
                                                <p className="text-base font-semibold leading-4 text-center md:text-left text-gray-800">Receptor</p>
                                                <p className="flex text-base font-semibold leading-4  text-left text-gray-800"><UserIcon className=' flex h-5 w-5'/>{order && order.full_name}</p>
                                            </div>
                                        </div>

                                        <div className="flex justify-center  md:justify-start items-center space-x-4 py-4 border-b border-gray-200 w-full">
                                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                                <path d="M19 5H5C3.89543 5 3 5.89543 3 7V17C3 18.1046 3.89543 19 5 19H19C20.1046 19 21 18.1046 21 17V7C21 5.89543 20.1046 5 19 5Z" stroke="#1F2937" strokeLinecap="round" strokeLinejoin="round" />
                                                <path d="M3 7L12 13L21 7" stroke="#1F2937" strokeLinecap="round" strokeLinejoin="round" />
                                            </svg>
                                            <p className="cursor-pointer text-sm leading-5 text-gray-800">{order && order.email}</p>
                                        </div>
                                    </div>
                                    <div className="flex justify-between xl:h-full  items-stretch w-full flex-col mt-6 md:mt-0">
                                        <div className="flex justify-center md:justify-start xl:flex-col flex-col md:space-x-6 lg:space-x-8 xl:space-x-0 space-y-4 xl:space-y-12 md:space-y-0 md:flex-row  items-center md:items-start ">
                                            <div className="flex justify-center md:justify-start  items-center md:items-start flex-col space-y-4 xl:mt-8">
                                                <p className="text-base font-semibold leading-4 text-center md:text-left text-gray-800">Dirección</p>
                                                <p className="w-48 lg:w-full xl:w-48 text-center md:text-left text-md leading-5 text-gray-600">{order && order.address_line_1},</p>
                                                <p className="w-48 lg:w-full xl:w-48 text-center md:text-left text-md leading-5 text-gray-600">{order && order.city}, {order && order.country_region}</p>
                                                <p className="w-48 lg:w-full xl:w-48 text-center md:text-left text-md leading-5 text-gray-600">{order && order.telephone_number}</p>
                                                
                                            </div>
                                        </div>
                                    </div>
                                    {/*<div className="flex justify-center md:flex-row flex-col items-stretch w-full space-y-4 md:space-y-0 md:space-x-6 xl:space-x-8">
                                    <div className="flex flex-col px-4 py-6 md:p-6 xl:p-8 w-full bg-gray-50 space-y-6  ">*/}
                                    <div className="flex justify-between xl:h-full  items-stretch w-full flex-col md:mt-0">
                                        <div className=" justify-center md:justify-start  flex-col mt-6 md:space-x-6 lg:space-x-8 xl:space-x-0 space-y-4 xl:space-y-12 md:space-y-0 md:flex-row  items-center md:items-start ">
                                        <h3 className="text-xl font-semibold leading-5 mb-4 text-gray-800">Sumario</h3>
                                        <div className="flex-row  w-full mt-4 space-y-4  border-gray-200 border-b pb-4">
                                            <div className="flex justify-between  w-full">
                                                <p className="flex text-base leading-4 text-gray-800">Subtotal</p>
                                                <p className="mr-10 flex-base leading-4 text-gray-600">${order && order.amount}</p>
                                            </div>
                                            <div className=" flex justify-between items-center w-full">
                                                <p className="flex text-base leading-4 text-gray-800">Envio</p>
                                                <p className="mr-10 flex text-base leading-4 text-gray-600">Por pagar</p>
                                            </div>
                                        </div>
                                        <div className="flex justify-between  items-center w-full">
                                            <p className="flex text-base font-semibold leading-4 text-gray-800">Total</p>
                                            <p className="mr-10 flex text-base font-semibold leading-4 text-gray-600">${order && order.amount}</p>
                                        </div>
                                    </div>
                                    
                                
                                    </div>
                                    {order && order.status === 'no procesado'? <Button onClick={buy(order)} className='visible relative mt-10 xl:hidden obsolute ml-12 items-center w-9/12'>Pagar</Button>:""}
                                </div>
                            </div>
                        </div>
                      </div>
                    </div>
                </div>
                </div>
                        </div>
                    </div>
              </div>
          </div>
        </Layout>
        </>
    )
}

const mapStateToProps=state=>({
    order: state.Orders.order,
    isAuthenticated: state.Auth.isAuthenticated,
    user: state.Auth.user,
    shipping:state.Shipping.shipp,
    url: state.Payment.url,
    loading: state.Payment.loading,
    payment: state.Payment.made_payment,

})

export default connect(mapStateToProps,{process_repayment_auth, reset ,list_orders, get_order_detail}) (OrdeDetail)