import {useEffect, useState} from "react";
import Footer from "../../components/navigation/footer";
import NavbarHero from "../../components/navigation/navbarheroiconv1";
import Layout from "../../hocs/layout/layout";
import logo from '/logorayadito1.png'
import { connect } from "react-redux";
import { signup } from "../../redux/action/auth";
import { Link, Navigate } from "react-router-dom";
import styled from "styled-components";
import logoG from "/icons8-logo-de-google.svg"
import axios from 'axios';
function Register({
    signup
}) {


    useEffect(() => {
        window.scrollTo(0, 0);
    }, [])

    const [formData, setFormData] = useState({
        first_name: '',
        last_name: '',
        email: '',
        password: '',
        re_password: ''
    })
    const [accountCreated, setAccountCreated] = useState(false);
    const {
        first_name,
        last_name,
        email,
        password,
        re_password
    } = formData;

    const onChange = e => setFormData({...formData,[e.target.name]: e.target.value});
    const onSubmit = e => {
        e.preventDefault();
        console.log(formData);
        signup(
            first_name,
            last_name,
            email,
            password,
            re_password
        )
        setAccountCreated(true)
        console.log(accountCreated);
        window.scrollTo(0, 0);
    }
    const signupWithGoogle = async () => {
        try {
            const res = await axios.get(`${import.meta.env.VITE_API_URL}/auth/o/google-oauth2/?redirect_uri=http://127.0.0.1:5173/`)

            window.location.replace(res.data.authorization_url)

        } catch (err) {
            console.log("Error logging in")
        }
    }
    if(accountCreated)
        return <Navigate to="/"/>;



    return (
        <>
         <Layout>
                <div className="min-h-full flex flex-col justify-center py-12 sm:px-6 lg:px-8">
                    <div className="sm:mx-auto sm:w-full sm:max-w-md">
                        <img className="mx-auto h-12 w-auto"
                            src={logo}
                            width={180}
                            alt="Workflow"/>
                        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">Registrate</h2>
                        <p className="mt-2 text-center text-sm text-gray-600">
                            o{' '}
                            <Link to="/login" className="font-medium text-indigo-600 hover:text-indigo-500">
                                ¿ya tienes una cuenta?
                            </Link>
                        </p>
                    </div>

                    <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
                        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
                            <form onSubmit={e=>onSubmit(e)} className="space-y-6">
                                <div>
                                    <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                                        Email
                                    </label>
                                    <div className="mt-1">
                                        <input  onChange={e=>onChange(e)} value={email} name="email" type="email" required className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"/>
                                    </div>
                                </div>
                                <div>
                                    <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                                        Ingrese su nombre
                                    </label>
                                    <div className="mt-1">
                                        <input name="first_name" onChange={e=>onChange(e)} value={first_name} type="text" required className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"/>
                                    </div>
                                </div>
                                <div>
                                    <label htmlFor="ape" className="block text-sm font-medium text-gray-700">
                                        Ingrese su apellido
                                    </label>
                                    <div className="mt-1">
                                        <input name="last_name" onChange={e=>onChange(e)} value={last_name} type="text" required className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"/>
                                    </div>
                                </div>

                                <div>
                                    <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                                        Contraseña
                                    </label>
                                    <div className="mt-1">
                                        <input  value={password} onChange={e=>onChange(e)} name="password"  type="password" required className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"/>
                                    </div>
                                </div>
                                <div>
                                    <label htmlFor="repassword" className="block text-sm font-medium text-gray-700">
                                        Confirma contraseña
                                    </label>
                                    <div className="mt-1">
                                        <input  value={re_password} onChange={e=>onChange(e)} name="re_password"  type="password" required className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"/>
                                    </div>
                                </div>
                                <div>
                                    <button type="submit" className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                                        Sign in
                                    </button>
                                </div>
                                
                            </form>
                            <div className="w-full flex items-center justify-between py-5">
                        <hr className="w-full bg-gray-400" />
                        <p className="text-base font-medium leading-4 px-2.5 text-gray-400">OR</p>
                        <hr className="w-full bg-gray-400  " />
                    </div>
                            <button onClick={signupWithGoogle} aria-label="Continue with google" role="button" className="focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-gray-700 py-3.5 px-4 border rounded-lg border-gray-700 flex items-center w-full ">
                                    <svg width={19} height={20} viewBox="0 0 19 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M18.9892 10.1871C18.9892 9.36767 18.9246 8.76973 18.7847 8.14966H9.68848V11.848H15.0277C14.9201 12.767 14.3388 14.1512 13.047 15.0812L13.0289 15.205L15.905 17.4969L16.1042 17.5173C17.9342 15.7789 18.9892 13.221 18.9892 10.1871Z" fill="#4285F4" />
                                        <path d="M9.68813 19.9314C12.3039 19.9314 14.4999 19.0455 16.1039 17.5174L13.0467 15.0813C12.2286 15.6682 11.1306 16.0779 9.68813 16.0779C7.12612 16.0779 4.95165 14.3395 4.17651 11.9366L4.06289 11.9465L1.07231 14.3273L1.0332 14.4391C2.62638 17.6946 5.89889 19.9314 9.68813 19.9314Z" fill="#34A853" />
                                        <path d="M4.17667 11.9366C3.97215 11.3165 3.85378 10.6521 3.85378 9.96562C3.85378 9.27905 3.97215 8.6147 4.16591 7.99463L4.1605 7.86257L1.13246 5.44363L1.03339 5.49211C0.37677 6.84302 0 8.36005 0 9.96562C0 11.5712 0.37677 13.0881 1.03339 14.4391L4.17667 11.9366Z" fill="#FBBC05" />
                                        <path d="M9.68807 3.85336C11.5073 3.85336 12.7344 4.66168 13.4342 5.33718L16.1684 2.59107C14.4892 0.985496 12.3039 0 9.68807 0C5.89885 0 2.62637 2.23672 1.0332 5.49214L4.16573 7.99466C4.95162 5.59183 7.12608 3.85336 9.68807 3.85336Z" fill="#EB4335" />
                                    </svg>
                                    <p className="text-base font-medium ml-4 text-gray-700">Continue with Google</p>
                                </button>
                        </div>
                    </div>
                </div>
            </Layout>
        </>
    )
}


const mapStateToProps = state => ({

})
export default connect(mapStateToProps,{
    signup
})(Register)

