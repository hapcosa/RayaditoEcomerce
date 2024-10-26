import { TrashIcon } from "@heroicons/react/24/outline";
import { PencilSquareIcon } from "@heroicons/react/24/solid";
import {
    Card,
    CardBody,
    CardFooter,
    Typography,
    Button,
  } from "@material-tailwind/react";

const Address= ({data, edit, delete_user_profile}) => {
  const del = (Id) => {
  
    console.log('in del')
    delete_user_profile(
        Id
    );
    window.scrollTo(0, 0);
    }
    return (
      <Card className="border border-gray-300 mt-6 lg:w-72 sm:w-96 xl:my-5 xl:w-96 2xl:w-96 md:w-64 bg-blue-gray-50 ">
        <CardBody>
          <Typography variant="h5" color="blue-gray" className="mb-2">
            {data.address_line_1}, {data.city}
          </Typography>
          <Typography>
          <ul>
            <li>
            {data.first_name} {data.last_name} 
            </li>
            <li>
              Región:{data.country_Region} Los lagos
            </li>
            <li>
              Telefono: {data.phone} 
            </li>
            <li>
              Codigo postal: {data.zipcode} 
            </li>
          </ul>
           
          </Typography>
        </CardBody>
        <CardFooter className="pt-0">
          <button className="py-1 px-2 rounded-md ml-1 mr-1 bg-blue-gray-100  hover:bg-blue-gray-200"><PencilSquareIcon className="text-indigo-400 w-4 h-4"/></button>
          <button onClick={del(del)} className="py-1 px-2 rounded-md ml-1 mr-1 bg-blue-gray-100  hover:bg-blue-gray-200"><TrashIcon className="w-4 h-4 text-red-600"/></button>
        </CardFooter>
      </Card>
    );
  }

export default Address;