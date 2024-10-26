
import logo from '/logostarken.jpg'

const Shippingbox=({shipping})=>{
    return(
        <>
            <div className="flex  w-full  md:p-6 xl:p-8  bg-gray-50 space-y-6   ">
        
                        <div className="flex justify-center items-start w-full">
                             <div className="flex justify-center items-center space-x-4">
                                    <div class="w-8 h-8">
                                        <img class="w-full h-full" alt="logo" src={shipping && shipping.photo} />
                                    </div>
                                    <div className="flex flex-col justify-start items-center">
                                        <p className="text-lg leading-6 font-semibold text-gray-800">
                                            {shipping && shipping.name}
                                            <br />
                                            <span className="font-normal">{shipping && shipping.time_to_delivery}</span>
                                        </p>
                                    </div>
                                </div>
                                
                            </div>
                        </div>
        </>
    )

}
export default Shippingbox