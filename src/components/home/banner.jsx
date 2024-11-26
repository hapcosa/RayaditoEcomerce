
import { Typewriter } from 'react-simple-typewriter'



const BannerPromo=() =>{
    return (
      <>
        <div className='flex items-center sm:mx-32 lg:mx-72'>
        <div className="pt-8 item-center pb-10 sm:pt-20 sm:pb-8 lg:pt-10 lg:pb-4">
        <div className="max-w-7xl  px-4 sm:px-6 lg:px-8 ">
            <div className=" py-2">
              <h3 className=" font font-extrabold tracking-tight text-gray-700 sm:text-6xl">
              JOYAS Y PIEDRAS
              </h3>
              <h4 className=" mx-2 text-4xl font font-extrabold tracking-tight text-gray-500 sm:text-5xl">
              <Typewriter words={
                  ['de autor', 'trabajadas a mano', 'para siempre', ]
                      }
                      loop={0}
                      cursor
                      cursorStyle='_'
                      typeSpeed={100}
                      deleteSpeed={50}
                      delaySpeed={1400}/>
              </h4>
              <p className="mt-6 text-xl text-gray-500">
                Joyas de autor, con piedras recolectadas en los hermosos y reconditos paisajes de la isla de Chiloe
              </p>
            </div>
          </div>
        </div>

        </div>
        
  
      </>
      
    )
  }
  export default BannerPromo
/*                <div
                  aria-hidden="true"
                  className="pointer-events-none lg:absolute lg:inset-y-0 lg:max-w-7xl lg:mx-auto lg:w-full"
                >
                  <div className="absolute transform sm:left-1/2 py-10 sm:top-0 sm:translate-x-8 lg:left-1/2 lg:top-1/2 lg:-translate-y-1/2 lg:translate-x-8">
                    <div className="flex items-center space-x-6 lg:space-x-8">
                      <div className="flex-shrink-0 grid grid-cols-1 gap-y-6 lg:gap-y-8">
                        <div className="w-36 h-44 rounded-lg overflow-hidden sm:opacity-0 lg:opacity-100">
                          <img
                            src={logo}
                            alt=""
                            className="w-full h-full object-center object-cover"
                          />
                        </div>
                        <div className="w-36 h-44 rounded-lg overflow-hidden">
                          <img
                            src={logo2}
                            alt=""
                            className="w-full h-full object-center object-cover"
                          />
                        </div>
                      </div>
                      <div className="flex-shrink-0 grid grid-cols-1 gap-y-6 lg:gap-y-8">
                        <div className="w-36 h-44 rounded-lg overflow-hidden">
                          <img
                            src={logo1}
                            alt=""
                            className="w-full h-full object-center object-cover"
                          />
                        </div>
                        <div className="w-36 h-44 rounded-lg overflow-hidden">
                          <img
                            src={logo3}
                            alt=""
                            className="w-full h-full object-center object-cover"
                          />
                        </div>
                        <div className="w-36 h-44 rounded-lg overflow-hidden">
                          <img
                            src={logo4}
                            alt=""
                            className="w-full h-full object-center object-cover"
                          />
                        </div>
                      </div>
                      <div className="flex-shrink-0 grid grid-cols-1 gap-y-6 lg:gap-y-8">
                        <div className="w-36 h-44 rounded-lg overflow-hidden">
                          <img
                            src={logo5}
                            alt=""
                            className="w-full h-full object-center object-cover"
                          />
                        </div>
                        <div className="w-36 h-44 rounded-lg overflow-hidden">
                          <img
                            src={logo6}
                            alt=""
                            className="w-full h-full object-center object-cover"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>*/