import { Link } from "react-router-dom"
import {

    CalendarIcon,


  } from '@heroicons/react/24/outline'
  import { IdentificationIcon, CreditCardIcon, UserIcon } from '@heroicons/react/24/solid'

  function classNames(...classes) {
    return classes.filter(Boolean).join(' ')
  }
const DashboardLink =()=>{
    return(
        <>
            <Link
            to="/dashboard"
            className={classNames('text-gray-600 hover:bg-gray-50 hover:text-gray-900',
                'group flex items-center px-2 py-2 text-base font-medium rounded-md'
            )}
            >
            <UserIcon
                className={classNames(
                'mr-4 flex-shrink-0 h-6 w-6 text-gray-400 group-hover:text-gray-500',
                )}
                aria-hidden="true"
            />
            Informacion de perfil
            </Link>
            
            <Link
            to="/dashboard/payments"
            className={classNames('text-gray-600 hover:bg-gray-50 hover:text-gray-900',
                'group flex items-center px-2 py-2 text-base font-medium rounded-md'
            )}
            >
            <CreditCardIcon
                className={classNames(
                'mr-4 flex-shrink-0 h-6 w-6 text-gray-400 group-hover:text-gray-500',
                )}
                aria-hidden="true"
            />
            Historial de pedidos
            </Link>
            
            <Link
            to="/dashboard/profile"
            className={classNames('text-gray-600 hover:bg-gray-50 hover:text-gray-900',
                'group flex items-center px-2 py-2 text-base font-medium rounded-md'
            )}
            >
            <IdentificationIcon
                className={classNames(
                'mr-4 flex-shrink-0 h-6 w-6 text-gray-400 group-hover:text-gray-500',
                )}
                aria-hidden="true"
            />
            Direcciones
            </Link>
        </>
    )
}

export default DashboardLink