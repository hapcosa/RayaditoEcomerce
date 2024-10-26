import React from "react";
import Layout from '../../hocs/layout/layout';
import { connect } from 'react-redux'
import {list_orders} from '../../redux/action/orders'
import {get_user_profiles} from '../../redux/action/profile'
import { useNavigate, Link  } from "react-router-dom";
import {
    get_items,
    get_total,
    get_item_total
} from "../../redux/action/cart";
import { useEffect } from 'react';
import { Navigate } from 'react-router';
import { load_user } from '../../redux/action/auth'
import {  useState } from 'react'
import { BuildingStorefrontIcon, CreditCardIcon, UserIcon } from "@heroicons/react/24/outline";
import {  Bars3Icon } from "@heroicons/react/24/solid";
const Perfile=({
    list_orders,
    get_items,
    get_total,
    get_item_total,
    get_user_profiles,
    isAuthenticated,
    user,
    load_user,

})=> {
    const [show, setShow] = useState(false);
    const navigate = useNavigate();
    useEffect(() => {
        get_items()
        get_total()
        get_item_total()
        list_orders()
        get_user_profiles()
        load_user()
    }, [])
    if(!isAuthenticated && user === null)
        return <Navigate to="/"/>


    return (
        <Layout>
            <div className="w-full h-full bg-gray-100">
                <div className="flex flex-no-wrap">
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
                                    
                                        <div id="closeSideBar" className="ml-48   mt-2 flex items-center justify-center  w-10" onClick={() => setShow(!show)}>
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
                                <div className="w-full">
                                    <div className="flex justify-center mb-4 w-full px-6">
                                        <div className="relative w-full">
                                            <div className="text-gray-500 absolute ml-4 inset-0 m-auto w-4 h-4">
                                                <svg xmlns="http://www.w3.org/2000/svg" className="icon icon-tabler icon-tabler-search" width={16} height={16} viewBox="0 0 24 24" strokeWidth={1} stroke="#A0AEC0" fill="none" strokeLinecap="round" strokeLinejoin="round">
                                                    <path stroke="none" d="M0 0h24v24H0z" />
                                                    <circle cx={10} cy={10} r={7} />
                                                    <line x1={21} y1={21} x2={15} y2={15} />
                                                </svg>
                                            </div>
                                            <input className="bg-gray-200 focus:outline-none rounded w-full text-sm text-gray-500  pl-10 py-2" type="text" placeholder="Search" />
                                        </div>
                                    </div>
                                    <div className="border-t border-gray-300">
                                        <div className="w-full flex items-center justify-between px-6 pt-1">
                                            <div className="flex items-center">
                                                <img alt="profile-pic" src="https://tuk-cdn.s3.amazonaws.com/assets/components/boxed_layout/bl_1.png" className="w-8 h-8 rounded-md" />
                                                <p className="md:text-xl text-gray-800 text-base leading-4 ml-2">Jane Doe</p>
                                            </div>
                                            <ul className="flex">
                                                <li className="cursor-pointer text-white pt-5 pb-3">
                                                    <svg xmlns="http://www.w3.org/2000/svg" className="icon icon-tabler icon-tabler-messages" width={24} height={24} viewBox="0 0 24 24" strokeWidth={1} stroke="#718096" fill="none" strokeLinecap="round" strokeLinejoin="round">
                                                        <path stroke="none" d="M0 0h24v24H0z" />
                                                        <path d="M21 14l-3 -3h-7a1 1 0 0 1 -1 -1v-6a1 1 0 0 1 1 -1h9a1 1 0 0 1 1 1v10" />
                                                        <path d="M14 15v2a1 1 0 0 1 -1 1h-7l-3 3v-10a1 1 0 0 1 1 -1h2" />
                                                    </svg>
                                                </li>
                                                <li className="cursor-pointer text-white pt-5 pb-3 pl-3">
                                                    <svg xmlns="http://www.w3.org/2000/svg" className="icon icon-tabler icon-tabler-bell" width={24} height={24} viewBox="0 0 24 24" strokeWidth={1} stroke="#718096" fill="none" strokeLinecap="round" strokeLinejoin="round">
                                                        <path stroke="none" d="M0 0h24v24H0z" />
                                                        <path d="M10 5a2 2 0 0 1 4 0a7 7 0 0 1 4 6v3a4 4 0 0 0 2 3h-16a4 4 0 0 0 2 -3v-3a7 7 0 0 1 4 -6" />
                                                        <path d="M9 17v1a3 3 0 0 0 6 0v-1" />
                                                    </svg>
                                                </li>
                                            </ul>
                                        </div>
                                    </div>
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
                        <div className="container mx-auto py-10 h-64 md:w-4/5 w-11/12 px-6">
                            {/* Remove class [ border-dashed border-2 border-gray-300 ] to remove dotted border */}
                            <div className="w-full h-full ">
                                <main className="flex-1">
                                    <div className="py-6">
                                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                                    {/* We've used 3xl here, but feel free to try other max-widths based on your needs */}
                                    <div className="max-w-3xl mx-auto">
                                    <div>
                                        <h3 className="text-lg leading-6 font-medium text-gray-900">Informacion de usuario</h3>
                                        <p className="mt-1 max-w-2xl text-sm text-gray-500">informacion.</p>
                                    </div>
                                    <div className="mt-5 border-t border-gray-200">
                                        <dl className="divide-y divide-gray-200">
                                        <div className="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4">
                                            <dt className="text-sm font-medium text-gray-500">Nombre:</dt>
                                            <dd className="mt-1 flex text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                                            <span className="flex-grow">{user.first_name}</span>
                                    
                                        </dd>
                                    
                                    </div>
                                    <div className="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4">
                                        <dt className="text-sm font-medium text-gray-500">Apellido:</dt>
                                        <dd className="mt-1 flex text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                                        <span className="flex-grow">{user.last_name}</span>
                                        
                                        </dd>
                                    </div>

                                
                                    <div className="border-b py-4 sm:grid sm:py-5 sm:grid-cols-3 sm:gap-4">
                                        <dt className="text-sm font-medium text-gray-500">Email:</dt>
                                        <dd className="mt-1 flex text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                                        <span className=" flex-grow">{user.email}</span>
                                        
                                        </dd>
                                        
                                    </div>

                                
                                        </dl>
                                     </div>
                                    </div>
                                    </div>
                                    </div>
                                </main>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        </Layout>
    );
}
const mapStateToProps =state=>({
    orders: state.Orders.orders,
    isAuthenticated: state.Auth.isAuthenticated,
    user: state.Auth.user,
    profile: state.Auth.profile
})

export default connect(mapStateToProps,{
    list_orders,
    get_items,
    get_total,
    get_item_total,
    get_user_profiles,
    load_user
}) (Perfile)