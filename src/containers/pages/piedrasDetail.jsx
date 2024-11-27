import { connect } from "react-redux"
import { Link,  } from "react-router-dom"
import Rater from "react-rater";
import { Rings } from 'react-loader-spinner';
import "react-rater/lib/react-rater.css";
import Layout from "../../hocs/layout/layout"
import { useParams, useNavigate} from "react-router-dom"
import { useEffect, useState } from "react"
import { get_category } from "../../redux/action/categories"
import { get_piedras_id, get_related_piedras, get_piedras_id_galery} from "../../redux/action/piedras"

import Galery from "../../components/product/galery"

import {get_items, add_item, get_total, get_item_total} from "../../redux/action/cart"

const PiedrasDetail = ({
    get_piedras_id,
    piedra,
    piedra_galery,
    get_piedras_id_galery,
    get_items,
    add_item,
    get_total,
    get_item_total,
    category,
    get_category,
    related_piedras
}) =>{
  
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
        if (piedra && piedra !== null && piedra !== undefined && piedra.sold === false) {
          setLoading(true);
          await add_item(piedra);
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
        get_piedras_id(productId)
        get_piedras_id_galery(productId)
        get_category(piedra && piedra.category)
        get_related_piedras(productId)
    
    }, []);
    
      return (
        <Layout>
        <section className="container flex-grow mx-auto max-w-[1200px] border-b py-5 lg:grid lg:grid-cols-2 lg:py-10">
          {/* image gallery */}
          <div className="container mx-auto px-4">
          <Galery data={piedra && piedra.photo} galery={piedra_galery && piedra_galery}/>
    
            {/* /image gallery  */}
          </div>
          {/* description  */}
    
          <div className="  sm:mx-2 md:mx-8  px-5 lg:px-5">
            <h2 className="pt-3 text-2xl font-bold lg:pt-0">
              {piedra && piedra.name}
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
              {piedra && piedra.sold ? (
                <span className="text-red-600">Agotado</span>
                
              ) : (
                <span className="text-green-600">Si </span>
                
              )}
            </p>
            <p className="font-bold">
              Material: {""}
               <span className="font-normal">{piedra && piedra.material}</span>
            </p>
            <p className="font-bold">
              Categoria:{" "}
              <span className="font-normal">{category && category.name}</span>
            </p>
            <p className="font-bold">
              SKU: <span className="font-normal">000010{piedra && piedra.id}</span>
            </p>
            <p className="mt-4 text-4xl font-bold text-violet-900">
              ${piedra && piedra.price}{" "}
              <span className="text-xs text-gray-400 line-through">
                ${piedra && piedra.compareprice}
              </span>
            </p>
            <p className="pt-5 text-sm leading-5 text-gray-500">
              {piedra && piedra.description}
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
            {piedra && piedra.sold?
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
          {related_piedras &&
                related_piedras !== null &&
                related_piedras !== undefined  ?
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
             {related_piedras &&
                related_piedras !== null &&
                related_piedras !== undefined &&
                 related_piedras.map((piedra) => (
                  <div key={piedra.id} className="group relative bg-cover">
                    <div className="mt-5 w-80 min-h-40 bg-gray-200  rounded-md overflow-hidden group-hover:opacity-75 lg:h-52 lg:aspect-none">
                      <img
                        src={piedra && piedra.photo}
                        alt=""
                        className="w-full h-full object-center object-cover lg:w-full lg:h-full"
                      />
                    </div>
                    <div className=" group-hover:opacity-75 w-44 mt-2 justify-between">
                      <div>
                        <h3 className="text-sm text-gray-700">
                          <Link  onClick={()=>{window.open(`${window.location.origin}/piedras/${piedra.id}`)}} >
                          
                            <span aria-hidden="true" className="absolute inset-0" />
                            {piedra && piedra.name}
                          </Link>
                        </h3>
                      </div>
                      <p className="text-sm font-medium text-gray-500">{piedra.price} clp</p>
                    </div>
                  </div>
                ))}
          </Carousel>:<h1>no hay mas productos relacionados</h1>}
        </section>
        
        </Layout>
      );
    }
    
const mapStateToProps = state => ({ 
    piedra: state.Piedras.piedra,
    related_piedras: state.Piedras.related_piedras,
    piedra_galery: state.Piedras.piedra_galery,
    category: state.Categories.category
})
export default connect(mapStateToProps, { get_category, get_piedras_id, get_related_piedras, get_piedras_id_galery, get_items, add_item, get_total, get_item_total}) (PiedrasDetail)