import React from "react";
import agatas from "/home/obrero/RayaditoWeb/public/DSC_1826-removebg-preview.png"
import colgant from "/IMG_20241103_154257-removebg-preview.png"
import {Link} from 'react-router-dom'
const Banner = () => {
    return (
        <div className="container mx-auto py-9 md:py-4 px-4 md:px-6">
            <div className="flex items-strech justify-center flex-col md:flex-row space-y-2 md:space-y-0 md:space-x-6 lg:space-x-2">
                <Link to="/joyas" className="flex flex-col md:flex-row items-strech justify-between bg-gray-50 py-6 px-6 md:py-12 lg:px-12 md:w-8/12 lg:w-7/12 xl:w-8/12 2xl:w-9/12">
                    <div className="flex flex-col justify-center md:w-1/2">
                        <h1 className="text-7xl lg:text-5xl font-semibold text-gray-800">Joyas</h1>
                        <p className="text-base lg:text-xl text-gray-800">
                             Joyas de plata
                        </p>
                    </div>
                    <div className="md:w-1/2 mt-8 md:mt-0 flex justify-center ">
                        <img src={colgant} alt="" className="md:w-80 md:h-80 lg:w-120 lg:h-120"/>
                    </div>
                </Link>
                <Link  to="/piedras" className="md:w-4/12 lg:w-5/12 xl:w-4/12 2xl:w-3/12 bg-gray-50 py-6 px-6 md:py-0 md:px-4 lg:px-6 flex flex-col justify-center relative">
                    <div className="flex flex-col justify-center">
                        <h1 className="text-3xl lg:text-4xl font-semibold text-gray-800">Piedras</h1>
                        <p className="text-base lg:text-xl text-gray-800">
                            Piedras semi preciosas
                        </p>
                    </div>
                    <div className="flex justify-end md:absolute md:bottom-4 md:right-4 lg:bottom-0 lg:right-0">
                        <img src={agatas} alt=""  className="md:w-80 md:h-80 lg:w-40 lg:h-40" />
                    </div>
                </Link>
            </div>
        </div>
    );
};
export default Banner