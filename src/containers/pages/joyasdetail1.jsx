import { Link, Navigate } from "react-router-dom"
import Rater from "react-rater";
import { Rings } from 'react-loader-spinner';
import "react-rater/lib/react-rater.css";
import { connect } from "react-redux";
import Layout from "../../hocs/layout/layout";
import { useNavigate, useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { get_category } from "../../redux/action/categories";
import {
  get_joyas_id,
  get_related_joyas,
  get_joyas_id_galery,
  get_material
} from "../../redux/action/joyas";

import Galery from "../../components/product/galery";
import {
  get_items,
  add_item,
  get_total,
  get_item_total,
} from "../../redux/action/cart";
import { ShoppingBagIcon } from "@heroicons/react/24/solid";
import Carousel from 'react-multi-carousel';
import 'react-multi-carousel/lib/styles.css';

const JoyasDetailDos = ({
  get_joyas_id,
  joya,
  joya_galery,
  get_joyas_id_galery,
  add_item,
  get_items,
  get_total,
  get_item_total,
  category,
  material,
  get_category,
  get_material,
  get_related_joyas,
  related_joyas

}) => {
  const responsive = {
    superLargeDesktop: {
      // the naming can be any, depends on you.
      breakpoint: { max: 4000, min: 3000 },
      items: 4
    },
    desktop: {
      breakpoint: { max: 3000, min: 1024 },
      items: 3
    },
    tablet: {
      breakpoint: { max: 1024, min: 464 },
      items: 2
    },
    mobile: {
      breakpoint: { max: 464, min: 0 },
      items: 1
    }
  };

  
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const addToCart = async () => {
    if (joya && joya !== null && joya !== undefined && joya.sold === false) {
      setLoading(true);
      await add_item(joya);
      await get_items();
      await get_total();
      await get_item_total();
      setLoading(false);
      navigate("/cart");
    }
  };

  const params = useParams()
  const productId = params.productId
  useEffect(() => {
    
    console.log("useffect")
    window.scrollTo(0, 0);
    get_joyas_id(productId)
    get_joyas_id_galery(productId)
    get_category(joya.category)
    get_related_joyas(productId)
    get_category(joya.category)

}, []);

  return (
    <Layout>
    <section className="container flex-grow mx-auto max-w-[1200px] border-b py-5 lg:grid lg:grid-cols-2 lg:py-10">
      {/* image gallery */}
      <div className="container mx-auto px-4">
      <Galery data={joya && joya.photo} galery={joya_galery && joya_galery}/>

        {/* /image gallery  */}
      </div>
      {/* description  */}

      <div className="  sm:mx-2 md:mx-8  px-5 lg:px-5">
        <h2 className="pt-3 text-2xl font-bold lg:pt-0">
          {joya.name}
        </h2>
        <div className="mt-1">
          <div className="flex items-center">
            <Rater
              style={{ fontSize: "20px" }}
              total={5}
              interactive={false}
              rating={4.5}
            />
            <p className="ml-3 text-sm text-gray-400">
              (24)
            </p>
          </div>
        </div>
        <p className="mt-5 font-bold">
          Disponible:{" "}
          {joya.sold ? (
            <span className="text-red-600">Agotado</span>
            
          ) : (
            <span className="text-green-600">Si </span>
            
          )}
        </p>
        <p className="font-bold">
          Material: {""}
           <span className="font-normal">{joya.material}</span>
        </p>
        <p className="font-bold">
          Categoria:{" "}
          <span className="font-normal">{category.name}</span>
        </p>
        <p className="font-bold">
          SKU: <span className="font-normal">000010{joya.id}</span>
        </p>
        <p className="mt-4 text-4xl font-bold text-violet-900">
          ${joya.price}{" "}
          <span className="text-xs text-gray-400 line-through">
            ${joya.compareprice}
          </span>
        </p>
        <p className="pt-5 text-sm leading-5 text-gray-500">
          {joya.description}
        </p>
        {/*<div className="mt-6">
          <p className="pb-2 text-xs text-gray-500">Size</p>
          <div className= "flex gap-1">
            <div
              className="flex h-8 w-8 items-center justify-center   ring-gray-500 ">
            </div>
          </div>
        </div>*/}
        <div className="mt-7 flex flex-row items-center gap-6">
        {joya && joya.sold?
                   <p className="py-3 px-8 flex items-center justify-center text-base font-medium max-w-xs flex-1 text-red-600">No disponible</p>:
                    <button
                      type="submit"
                      onClick={addToCart}
                      className="max-w-xs flex-1 bg-gray-600 border border-transparent rounded-md py-3 px-8 flex items-center justify-center text-base font-medium text-white hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-50 focus:ring-indigo-500 sm:w-full"
                    >{loading?
                      <div className="flex items-center justify-center w-full h-full bg-gray-500 rounded-md">
                        <Rings width={20} height={20}/>
                      </div>:<p>agregar al carrito</p>
                    }
                      
                    </button>
                    }

         {/*<button className="flex h-12 w-1/3 items-center justify-center bg-amber-400 duration-100 hover:bg-yellow-300">
            <AiOutlineHeart className="mx-2" />
            Wishlist
          </button>*/ } 
        </div>
      </div>
      
    </section>
    <section className="mt-3 mx-10 mb-10">
    <div className="mt-6">
        <p className="text-2xl font-bold">
          Creaciones relacionadas: {""}
        </p>
      </div>
      {related_joyas &&
            related_joyas !== null &&
            related_joyas !== undefined  ?
      <Carousel
        swipeable={false}
        draggable={false}
        responsive={responsive}
        ssr={true} // means to render carousel on server-side.
        infinite={true}
        autoPlaySpeed={1000}
        keyBoardControl={true}
        transitionDuration={500}
        containerClass="carousel-container"
        removeArrowOnDeviceType={["tablet", "mobile"]}>
         {related_joyas &&
            related_joyas !== null &&
            related_joyas !== undefined &&
             related_joyas.map((joya) => (
              <div key={joya.id} className="group relative bg-cover">
                <div className="mt-5 w-80 min-h-40 bg-gray-200  rounded-md overflow-hidden group-hover:opacity-75 lg:h-52 lg:aspect-none">
                  <img
                    src={joya.photo}
                    alt=""
                    className="w-full h-full object-center object-cover lg:w-full lg:h-full"
                  />
                </div>
                <div className=" group-hover:opacity-75 w-44 mt-2 justify-between">
                  <div>
                    <h3 className="text-sm text-gray-700">
                      <Link  onClick={()=>{window.open(`${window.location.origin}/joyas/${joya.id}`)}} >
                      
                        <span aria-hidden="true" className="absolute inset-0" />
                        {joya.name}
                      </Link>
                    </h3>
                  </div>
                  <p className="text-sm font-medium text-gray-500">{joya.price} clp</p>
                </div>
              </div>
            ))}
      </Carousel>:<h1>no hay mas productos relacionados</h1>}
    </section>
    
    </Layout>
  );
}

const mapStateToProps = (state) => ({
  joya: state.Joyas.joya,
  related_joyas: state.Joyas.related_joyas,
  joya_galery: state.Joyas.joya_galery,
  material: state.Joyas.material,
  category: state.Categories.category,
  related_joyas: state.Joyas.related_joyas
})
export default connect(mapStateToProps, {
  get_joyas_id,
  get_related_joyas,
  get_joyas_id_galery,
  add_item,
  get_total,
  get_items,
  get_item_total,
  get_material,
  get_category,
  get_related_joyas
})(JoyasDetailDos)
