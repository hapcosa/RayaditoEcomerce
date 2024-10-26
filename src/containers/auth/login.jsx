import logo from '/logorayadito1.png'
import {useEffect, useState} from "react";
import { connect } from "react-redux";
import { Link, Navigate } from 'react-router-dom';
import Layout from "../../hocs/layout/layout";
import { login } from '../../redux/action/auth';
import { Rings } from 'react-loader-spinner';
import axios from 'axios';
function Login({ 
    login, loading
}) {
    useEffect(() => {
        window.scrollTo(0, 0);
    }, [])

    const [formData, setFormData] = useState({
        email: '',
        password: ''
    })
    const [verificated, setVerificated] = useState(false)
    const {

        email,
        password
    } = formData;

    const onChange = e => setFormData({...formData,[e.target.name]: e.target.value});
    
    const onSubmit = e => {
        e.preventDefault();
        login(email, password)
        setVerificated(true);
        window.scrollTo(0, 0);
        
    }
    const loginWithGoogle = async () =>{
        try{
            const res = await axios.get(`${import.meta.env.VITE_API_URL}/auth/o/google-oauth2/?redirect_uri=http://127.0.0.1:5173/`)
            window.location.replace(res.data.authorization_url)

        }catch(err){
            console.log(err)
            console.log("Error logging in")
        }
    }
    if (verificated && !loading)
        return <><Navigate to='/' /></>
    return(
        <>
        <Layout>

                <div className="min-h-full flex flex-col justify-center py-12 sm:px-6 lg:px-8">
                <div className="sm:mx-auto sm:w-full sm:max-w-md">
                        <img className="mx-auto h-12 w-auto"
                            src={logo}
                            width={180}
                            alt="Workflow"/>
                        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">Ingresa en tu cuenta</h2>
                        <p className="mt-2 text-center text-sm text-gray-600">
                            o{' '}
                            <Link to="/register" className="font-medium text-indigo-600 hover:text-indigo-500">
                                si no tienes, crea una cuenta
                            </Link>
                        </p>
                    </div>  

                    <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
                    <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
                        <form className="space-y-6" onSubmit={e=>onSubmit(e)}>
                        <div>
                            <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                            Email address
                            </label>
                            <div className="mt-1">
                            <input onChange={e=>onChange(e)}
                                value={email}
                                id="email"
                                name="email"
                                type="email"
                                autoComplete="email"
                                required
                                className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                            />
                            </div>
                        </div>

                        <div>
                            <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                            Password
                            </label>
                            <div className="mt-1">
                            <input
                                value={password} 
                                onChange={e=>onChange(e)}
                                id="password"
                                name="password"
                                type="password"
                                autoComplete="current-password"
                                required
                                className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                            />
                            </div>
                        </div>

                        <div className="flex items-center justify-between">
                            <div className="flex items-center">
                            <input
                                id="remember-me"
                                name="remember-me"
                                type="checkbox"
                                className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                            />
                            <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-900">
                                Remember me
                            </label>
                            </div>

                            <div className="text-sm">
                            <Link to="/reset_password" className="font-medium text-indigo-600 hover:text-indigo-500">
                                Forgot your password?
                            </Link>
                            </div>
                        </div>

                        <div>
                        {loading?
                            <button type="button" className=" mx-auto my-3 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-gray-600 hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                                <Rings color="#FFF" height={20} width={20} />
                            </button>:
                            <button
                            type="submit"
                            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                            >
                            login
                            </button>}
                        </div>
                        </form>
                        <div className="w-full flex items-center justify-between py-5">
                        <hr className="w-full bg-gray-400" />
                        <p className="text-base font-medium leading-4 px-2.5 text-gray-400">OR</p>
                        <hr className="w-full bg-gray-400  " />
                    </div>
                            <button aria-label="Continue with google" role="button" className="focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-gray-700 py-3.5 px-4 border rounded-lg border-gray-700 flex items-center w-full " onClick={loginWithGoogle}>
                                    <svg width={19} height={20} viewBox="0 0 19 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M18.9892 10.1871C18.9892 9.36767 18.9246 8.76973 18.7847 8.14966H9.68848V11.848H15.0277C14.9201 12.767 14.3388 14.1512 13.047 15.0812L13.0289 15.205L15.905 17.4969L16.1042 17.5173C17.9342 15.7789 18.9892 13.221 18.9892 10.1871Z" fill="#4285F4" />
                                        <path d="M9.68813 19.9314C12.3039 19.9314 14.4999 19.0455 16.1039 17.5174L13.0467 15.0813C12.2286 15.6682 11.1306 16.0779 9.68813 16.0779C7.12612 16.0779 4.95165 14.3395 4.17651 11.9366L4.06289 11.9465L1.07231 14.3273L1.0332 14.4391C2.62638 17.6946 5.89889 19.9314 9.68813 19.9314Z" fill="#34A853" />
                                        <path d="M4.17667 11.9366C3.97215 11.3165 3.85378 10.6521 3.85378 9.96562C3.85378 9.27905 3.97215 8.6147 4.16591 7.99463L4.1605 7.86257L1.13246 5.44363L1.03339 5.49211C0.37677 6.84302 0 8.36005 0 9.96562C0 11.5712 0.37677 13.0881 1.03339 14.4391L4.17667 11.9366Z" fill="#FBBC05" />
                                        <path d="M9.68807 3.85336C11.5073 3.85336 12.7344 4.66168 13.4342 5.33718L16.1684 2.59107C14.4892 0.985496 12.3039 0 9.68807 0C5.89885 0 2.62637 2.23672 1.0332 5.49214L4.16573 7.99466C4.95162 5.59183 7.12608 3.85336 9.68807 3.85336Z" fill="#EB4335" />
                                    </svg>
                                    <p className="text-base font-medium ml-4 text-gray-700">Continue with Google</p>
                                </button>

                        <div className="mt-6">
                        <div className="relative">
                            <div className="absolute inset-0 flex items-center">
                            <div className="w-full border-t border-gray-300" />
                            </div>
                            <div className="relative flex justify-center text-sm">
                            <span className="px-2 bg-white text-gray-500">Or continue with</span>
                            </div>
                        </div>

                        <div className="mt-6 grid grid-cols-3 gap-3">
                            <div>
                            <a
                                href="#"
                                className="w-full inline-flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-500 hover:bg-gray-50"
                            >
                                <span className="sr-only">Sign in with Facebook</span>
                                <svg className="w-5 h-5" aria-hidden="true" fill="currentColor" viewBox="0 0 20 20">
                                <path
                                    fillRule="evenodd"
                                    d="M20 10c0-5.523-4.477-10-10-10S0 4.477 0 10c0 4.991 3.657 9.128 8.438 9.878v-6.987h-2.54V10h2.54V7.797c0-2.506 1.492-3.89 3.777-3.89 1.094 0 2.238.195 2.238.195v2.46h-1.26c-1.243 0-1.63.771-1.63 1.562V10h2.773l-.443 2.89h-2.33v6.988C16.343 19.128 20 14.991 20 10z"
                                    clipRule="evenodd"
                                />
                                </svg>
                            </a>
                            </div>

                            <div>
                            <a
                                href="#"
                                className="w-full inline-flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-500 hover:bg-gray-50"
                            >
                                <span className="sr-only">Sign in with Twitter</span>
                                <svg className="w-5 h-5" aria-hidden="true" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M6.29 18.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0020 3.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.073 4.073 0 01.8 7.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 010 16.407a11.616 11.616 0 006.29 1.84" />
                                </svg>
                            </a>
                            </div>

                            <div>
                            <a
                                href="#"
                                className="w-full inline-flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-500 hover:bg-gray-50"
                            >
                                <span className="sr-only">Sign in with GitHub</span>
                                <svg className="w-5 h-5" aria-hidden="true" fill="currentColor" viewBox="0 0 20 20">
                                <path
                                    fillRule="evenodd"
                                    d="M10 0C4.477 0 0 4.484 0 10.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0110 4.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.203 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.942.359.31.678.921.678 1.856 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0020 10.017C20 4.484 15.522 0 10 0z"
                                    clipRule="evenodd"
                                />
                                </svg>
                            </a>
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
const mapStateToProps = state => ({
    loading: state.Auth.loading,
})
export default connect(mapStateToProps,{
    login
})(Login)
