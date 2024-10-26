import Layout from '../../hocs/layout/layout';
import { connect } from 'react-redux'
import {list_orders, get_order_detail} from '../../redux/action/orders'
import {
    get_items,
    get_total,
    get_item_total
} from "../../redux/action/cart";
import { useEffect } from 'react';
import { Navigate } from 'react-router';
import {  useState } from 'react'

import { Link } from 'react-router-dom';
import {
     process_repayment_auth, reset
  } from '../../redux/action/payment';

import TableOrders from '../../components/orders/tableorders';
import { BuildingStorefrontIcon, CreditCardIcon, UserIcon } from "@heroicons/react/24/outline";
import { Bars3Icon } from "@heroicons/react/24/solid";
const DashboardPayments =({
    list_orders,
    get_items,
    get_total,
    get_item_total,
    orders,
    isAuthenticated,
    made_payment,
    process_repayment_auth, 
    reset,
    url,
    loading,
    
})=>{
    const [show, setShow] = useState(false);


    useEffect(() => {
        get_items()
        get_total()
        get_item_total()
        list_orders()
    }, [])

    if(!isAuthenticated)
        return <Navigate to="/"/>
    
    if (made_payment){
        /*window.open(url, '_blank')*/
        made_payment = false
        reset()
        window.location.href = url
            
    }

    return (
        <Layout>
        <div>
          <div className="w-full h-full bg-gray-100">
              <div className="flex ">
                    {/* Sidebar starts */}
                    <div className="absolute lg:relative w-64 h-screen shadow bg-gray-300 hidden lg:block">

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
                    <div className={show ? "w-full h-full absolute z-40  transform  translate-x-0 " : "   w-full h-full absolute z-40  transform -translate-x-full"} id="mobile-nav">
                        <div className="bg-gray-800 opacity-50 absolute h-full w-full lg:hidden" onClick={() => setShow(!show)} />
                        <div className="absolute z-40 sm:relative w-64 md:w-64 shadow pb-4 bg-gray-300 lg:hidden transition duration-150 ease-in-out h-full">
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
                        <div className=" mx-auto py-10  md:w-4/5 w-11/12 px-6">
                            {/* Remove class [ brder-dashed border-2 border-gray-300 ] to remove dotted border */}
                            <div className="w-full h-full ">{/* Place your content here */}
                             <TableOrders orders={orders}
                                process_repayment_auth={process_repayment_auth}
                                reset={reset}
                             />
                            </div>
                        </div>
                    </div>
              </div>
          </div>
        
        
        
        </div>
      </Layout>
    )
}

const mapStateToProps =state=>({
    orders: state.Orders.orders,
    isAuthenticated: state.Auth.isAuthenticated,
    user: state.Auth.user,
    made_payment: state.Payment.made_payment,
    url: state.Payment.url,
    loading: state.Payment.loading,
})

export default connect(mapStateToProps,{
    list_orders,
    get_order_detail,
    get_items,
    get_total,
    get_item_total,
    process_repayment_auth, reset
}) (DashboardPayments)