import Layout from '../../hocs/layout/layout';
import { connect } from 'react-redux'
import {list_orders} from '../../redux/action/orders'
import {
    get_items,
    get_total,
    get_item_total
} from "../../redux/action/cart";
import { useEffect } from 'react';
import { useNavigate } from 'react-router';
import {Button,
} from "@material-tailwind/react";

import {  useState } from 'react'

import { Link } from 'react-router-dom';
import { countries } from '../../helpers/fixedCountries';
import { update_user_profile, get_user_profiles,create_user_profile } from '../../redux/action/profile';

import { BuildingStorefrontIcon, CreditCardIcon, UserIcon } from "@heroicons/react/24/outline";
import { Bars3BottomRightIcon, Bars3Icon } from "@heroicons/react/24/solid";


const DashboardUpdateAdress =({
    list_orders,
    get_items,
    get_total,
    get_item_total,
    orders,
    isAuthenticated,
    user,
    get_user_profiles,
    update_user_profile,
    create_user_profile,
    profiles
})=>{

    const [show, setShow] = useState(false);

    const [saved, setSaved] = useState(false)

    useEffect(() => {
        get_items()
        get_total()
        get_item_total()
        list_orders()
        get_user_profiles()
        get_user_profiles()
    }, [])

    const [formData, setFormData] = useState({
        address_line_1: '',
        city: '',
        zipcode: '',
        phone: '',
        country_region: ''
    });

    const {
        first_name,
        last_name,
        address_line_1,
        city,
        zipcode,
        phone,
        country_region
    } = formData;

    const onChange = e => setFormData({ ...formData, [e.target.name]: e.target.value });
    const navigate = useNavigate()
    const onSubmit = e => {
      e.preventDefault();
      setLoading(true)
      create_user_profile(
        first_name,
        last_name,
        address_line_1,
        city,
        zipcode,
        phone,
        country_region
      );
      setLoading(false)
      setSaved(true)
      window.scrollTo(0, 0);
  };
    if(saved) {
        navigate('/dashboard/profile')
    }
    if(!isAuthenticated)
       navigate('/')

    return (
        <Layout>
            <div>

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
                                    
                                    <main className=" border-spacing-1 mb-10 flex-1">
                                      <div className="py-6">
                                      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                                      <div className="bg-white px-4 py-5 border-b border-gray-200 sm:px-6 flex">
                                          <h1 className="text-lg leading-6 font-medium text-gray-700 flex-auto text">Nueva dirección</h1>
                                          <Link to='/dashboard/profile'><Button className='py-3 ml-5 bg-blue-gray-100 text-gray-600 rounded-xl flex-auto hover:bg-blue-gray-200'> Tus Direcciones</Button></Link>
                                        </div>

                                      {/* We've used 3xl here, but feel free to try other max-widths based on your needs */}
                                      <form onSubmit={e => onSubmit(e)} className="max-w-3xl mx-auto">
                                
                                  
                                      <div className="sm:grid sm:grid-cols-3 sm:gap-4 sm:items-start sm:border-t sm:border-gray-200 sm:pt-5">
                                          <label htmlFor="username" className="block text-sm font-medium text-gray-700 sm:mt-px sm:pt-2">
                                          Nombre
                                          </label>
                                          <div className="mt-1 sm:mt-0 sm:col-span-2">
                                            <div className="max-w-lg flex rounded-md shadow-sm">
                                              
                                              <input
                                                type="text"
                                                name='first_name'
                                                placeholder="Nombre de quien recibe el producto. Ej: Megumi"
                                                onChange={e => onChange(e)}
                                                value={first_name}
                                                className="flex-1 block w-full focus:ring-indigo-500 focus:border-indigo-500 min-w-0 rounded-md sm:text-sm border-gray-500"
                                              />
                                            </div>
                                          </div>
                                        </div>
                                        <div className="sm:grid sm:grid-cols-3 sm:gap-4 sm:items-start sm:border-t sm:border-gray-200 sm:pt-5">
                                          <label htmlFor="username" className="block text-sm font-medium text-gray-700 sm:mt-px sm:pt-2">
                                          Apellido
                                          </label>
                                          <div className="mt-1 sm:mt-0 sm:col-span-2">
                                            <div className="max-w-lg flex rounded-md shadow-sm">
                                              
                                              <input
                                                type="text"
                                                name='last_name'
                                                placeholder="ej: Fushiguro"
                                                onChange={e => onChange(e)}
                                                value={last_name}
                                                className="flex-1 block w-full focus:ring-indigo-500 focus:border-indigo-500 min-w-0 rounded-md sm:text-sm border-gray-500"
                                              />
                                            </div>
                                          </div>
                                        </div>

                                        <div className="sm:grid sm:grid-cols-3 sm:gap-4 sm:items-start sm:border-t sm:border-gray-200 sm:pt-5">
                                          <label htmlFor="username" className="block text-sm font-medium text-gray-700 sm:mt-px sm:pt-2">
                                          Direccion: 
                                          </label>
                                          <div className="mt-1 sm:mt-0 sm:col-span-2">
                                            <div className="max-w-lg flex rounded-md shadow-sm">
                                              
                                              <input
                                                type="text"
                                                name='address_line_1'
                                                placeholder='ej: General Baquedano451'
                                                onChange={e => onChange(e)}
                                                value={address_line_1}
                                                className="flex-1 block w-full focus:ring-indigo-500 focus:border-indigo-500 min-w-0 rounded-md sm:text-sm border-gray-500"
                                              />
                                            </div>
                                          </div>
                                        </div>
                                        
                                        

                                        <div className="sm:grid sm:grid-cols-3 sm:gap-4 sm:items-start sm:border-t sm:border-gray-200 sm:pt-5">
                                          <label htmlFor="username" className="block text-sm font-medium text-gray-700 sm:mt-px sm:pt-2">
                                          Ciudad
                                          </label>
                                          <div className="mt-1 sm:mt-0 sm:col-span-2">
                                            <div className="max-w-lg flex rounded-md shadow-sm">
                                              
                                              <input
                                                type="text"
                                                name='city'
                                                placeholder="Valdivia"
                                                onChange={e => onChange(e)}
                                                value={city}
                                                className="flex-1 block w-full focus:ring-indigo-500 focus:border-indigo-500 min-w-0 rounded-md sm:text-sm border-gray-500"
                                              />
                                            </div>
                                          </div>
                                        </div>

                                        

                                        <div className="sm:grid sm:grid-cols-3 sm:gap-4 sm:items-start sm:border-t sm:border-gray-200 sm:pt-5">
                                          <label htmlFor="username" className="block text-sm font-medium text-gray-700 sm:mt-px sm:pt-2">
                                          Postal Code/Zipcode: 
                                          </label>
                                          <div className="mt-1 sm:mt-0 sm:col-span-2">
                                            <div className="max-w-lg flex rounded-md shadow-sm">
                                              
                                              <input
                                                type="text"
                                                name='zipcode'
                                                      placeholder='ej: 5700000'
                                                      onChange={e => onChange(e)}
                                                      value={zipcode}
                                                className="flex-1 block w-full focus:ring-indigo-500 focus:border-indigo-500 min-w-0 rounded-md sm:text-sm border-gray-500"
                                              />
                                            </div>
                                          </div>
                                        </div>

                                        <div className="sm:grid sm:grid-cols-3 sm:gap-4 sm:items-start sm:border-t sm:border-gray-200 sm:pt-5">
                                          <label htmlFor="username" className="block text-sm font-medium text-gray-700 sm:mt-px sm:pt-2">
                                          Telefono: 
                                          </label>
                                          <div className="mt-1 sm:mt-0 sm:col-span-2">
                                            <div className="max-w-lg flex rounded-md shadow-sm">
                                              
                                              <input
                                                type="text"
                                                name='phone'
                                                      placeholder='ej: 950415XXX'
                                                      onChange={e => onChange(e)}
                                                      value={phone}
                                                className="flex-1 block w-full focus:ring-indigo-500 focus:border-indigo-500 min-w-0 rounded-md sm:text-sm border-gray-500"
                                              />
                                            </div>
                                          </div>
                                        </div>

                                        <div className="sm:grid sm:grid-cols-3 sm:gap-4 sm:items-start sm:border-t sm:border-gray-200 sm:pt-5">
                                          <label htmlFor="country" className="block text-sm font-medium text-gray-700 sm:mt-px sm:pt-2">
                                            Región
                                          </label>
                                          <div className="mt-1 sm:mt-0 sm:col-span-2">
                                                  <select
                                                      id='country_region' 
                                                      name='country_region'
                                                      onChange={e => onChange(e)}
                                                  >
                                                      <option value={country_region}>{profiles.country_region}</option>
                                                      {
                                                          countries && countries.map((country, index) => (
                                                              <option key={index} value={country.name}>{country.name}</option>
                                                          ))
                                                      }
                                                  </select>
                                          </div>
                                        </div>

                                        {loading?<button
                                          className="inline-flex mt-4 float-right items-center px-2.5 py-1.5 border border-transparent text-xs font-medium rounded shadow-sm text-white bg-blue-gray-200 hover:bg-blue-gray-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                                        >
                                          <Loader
                                          type="Oval"
                                          width={20}
                                          height={20}
                                          color="#fff"
                                          />
                                        </button>:<button
                                          type="submit"
                                          className="inline-flex mt-4 float-right items-center px-2.5 py-1.5 border border-transparent text-xs font-medium rounded shadow-sm text-white bg-blue-gray-200 hover:bg-blue-gray-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                                        >
                                          Guardar
                                        </button>}

                                      </form>
                                      </div>
                                      </div>
                                    </main>
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
    profiles: state.Profile.profiles,
})

export default connect(mapStateToProps,{
    list_orders,
    get_items,
    get_total,
    get_item_total,
    update_user_profile,
    get_user_profiles,
    create_user_profile
}) (DashboardUpdateAdress)