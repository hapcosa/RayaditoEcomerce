
import { Fragment, useEffect, useState } from 'react'
import { Dialog, Disclosure, Transition } from '@headlessui/react'
import { XMarkIcon } from '@heroicons/react/24/outline'
import {  FunnelIcon, MinusIcon, PlusIcon } from '@heroicons/react/24/solid'
import Layout from '../hocs/layout/layout'
import { get_categories_piedras, get_categories } from '../redux/action/categories'
import {get_piedras, get_filtered_piedras} from '../redux/action/piedras'
import { connect } from 'react-redux'
import ProductCard from '../components/product/cardproduct'
import {pricespiedras} from '../helpers/fixedPrices'


const Piedras=({
  categories,
  categories_piedras,
  get_categories,
  get_categories_piedras,
  get_piedras,
  piedras,
  get_filtered_piedras,
  filtered_piedras
}) => 
{
    const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false)
    const [filtered, setFiltered] = useState(false)
    const [formData, setFormData] = useState({
      category_id: '0',
      price_range:'any',
      sortBy: 'date_created', 
      order: 'desc'
    })

    const {
      category_id,
      price_range,
      sortBy,
      order
    } =formData

    useEffect(() => {
      window.scrollTo(0, 0);
      get_categories_piedras();
      get_piedras();
    },[])

    const onChange = e => setFormData({...formData,[e.target.name]: e.target.value})
    const onSubmit = e => {
      e.preventDefault()
      get_filtered_piedras(category_id,price_range, sortBy, order)
      setFiltered(true)

    }

    const showProducts = () => {
      let results = []
      let display = []

      if (
        filtered_piedras &&
        filtered_piedras !== null &&
        filtered_piedras !== undefined &&
        filtered
      ) {
        filtered_piedras.map((piedra, index) => {
            return display.push(
                <div key={piedra.id}>
                    <ProductCard data={piedra}
                      categories={categories && categories}
                      categories_piedras={categories && categories_piedras}/>
                </div>
            );
        });
      } else if (
          !filtered && 
          piedras &&
          piedras !== null && 
          piedras !== undefined
      ) {
          piedras.map((piedra, index) => {
            return display.push(
                <div key={piedra.id}>
                    <ProductCard data={piedra}
                      categories={categories && categories}
                      categories_piedras={categories && categories_piedras}/>
                </div>
            );
        }); 
      }

      for (let i = 0; i < display.length; i += 3) {
        results.push(
          <div key={i} className='grid md:grid-cols-3 '>
              {display[i] ? display[i] : <div className=''></div>}
              {display[i+1] ? display[i+1] : <div className=''></div>}
              {display[i+2] ? display[i+2] : <div className=''></div>}
          </div>
        )
      }

      if (results.length > 0){
        return results
      }else{
        return (<h1  >No existen piedras con esas especificaiones</h1>)
      }

    }

    return (
      <>
      <Layout>
      <div className="bg-white">
    <div>
      {/* Mobile filter dialog */}
      <Transition.Root show={mobileFiltersOpen} as={Fragment}>
        <Dialog as="div" className="fixed inset-0 flex z-40 lg:hidden" onClose={setMobileFiltersOpen}>
          <Transition.Child
            as={Fragment}
            enter="transition-opacity ease-linear duration-300"
            enterFrom="opacity-0"
            enterTo="opacity-100"
            leave="transition-opacity ease-linear duration-300"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            <Dialog.Overlay className="fixed inset-0 bg-black bg-opacity-25" />
          </Transition.Child>

          <Transition.Child
            as={Fragment}
            enter="transition ease-in-out duration-300 transform"
            enterFrom="translate-x-full"
            enterTo="translate-x-0"
            leave="transition ease-in-out duration-300 transform"
            leaveFrom="translate-x-0"
            leaveTo="translate-x-full"
          >
            <div className="ml-auto relative max-w-xs w-full h-full bg-white shadow-xl py-4 pb-12 flex flex-col overflow-y-auto">
              <div className="px-4 flex items-center justify-between">
                <h2 className="text-lg font-medium text-gray-900">Filtros</h2>
                <button
                  type="button"
                  className="-mr-2 w-10 h-10 bg-white p-2 rounded-md flex items-center justify-center text-gray-400"
                  onClick={() => setMobileFiltersOpen(false)}
                >
                  <span className="sr-only">Close menu</span>
                  <XMarkIcon className="h-6 w-6" aria-hidden="true" />
                </button>
              </div>

              {/* mobileFilters */}
              <form onSubmit={e=>onSubmit(e)} className="mt-4 border-gray-200">
                <h2 className="ml-2">Categorias</h2>
                <hr/>
                <ul role="list" className="text-sm font-medium text-gray-900 space-y-4 pb-6 border-b border-gray-200">
                <div  className='ml-2 flex items-center h-5 my-5'>
                      <input
                        onChange={e => onChange(e)}
                        value={0}
                        name='category_id'
                        type='radio'
                        className='focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded-full'
                        />
                      <label className="ml-2 min-w-0 flex-1 text-gray-500">
                        todo
                      </label>
                          </div>
              {
                      categories_piedras &&
                      categories_piedras !== null &&
                      categories_piedras !== undefined &&
                      categories_piedras.map(category => {
                          if (category.sub_categories.length === 0){
                              return (
                                <>
                                <hr/>
                                  <div key={category.id} className='ml-2 flex items-center h-5 my-5'>
                                      <input
                                          onChange={e => onChange(e)}
                                          value={category.id.toString()}
                                          name='category_id'
                                          type='radio'
                                          className='focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded-full'
                                      />
                                      <label className="ml-2 min-w-0 flex-1 text-gray-500">
                                          {category.name}
                                      </label>
                                  </div>

                                  </>
                              )
                          } else {
                              let result = []
                              result.push(
                                <>
                                <hr/>
                                <div key={category.id} className='ml-2 flex items-center my-5 h-5'>
                                      <input
                                          onChange={e => onChange(e)}
                                          value={category.id.toString()}
                                          name='category_id'
                                          type='radio'
                                          className='focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded-full'
                                      />
                                      <label className="ml-2  min-w-0 flex-1 text-gray-500">
                                          {category.name}
                                      </label>
                                  </div>
                                  <hr/>

                                </>
                                 
                              )

                              category.sub_categories.map(sub_category => {
                                  result.push(
                                    <>
                                      <div key={sub_category.id} className=' flex items-center h-5 ml-4 my-5'>
                                          <input
                                              onChange={e => onChange(e)}
                                              value={sub_category.id.toString()}
                                              name='category_id'
                                              type='radio'
                                              className='focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded-full'
                                          />
                                          <label className="ml-1 min-w-0 flex-1 text-gray-500">
                                              {sub_category.name}
                                          </label>
                                          
                                      </div>
                                      </>
                                      
                                  )
                              })

                              return result
                          }
                      })
                  }
              </ul>
                <Disclosure as="div" className="border-t border-gray-200 px-4 py-6">
                {({ open }) => (
                  <>
                  <h3 className="-mx-2 -my-3 flow-root">
                    <Disclosure.Button className="px-2 py-3 bg-white w-full flex items-center justify-between text-gray-400 hover:text-gray-500">
                      <span className="font-sofiapro-regular text-gray-900">Precios</span>
                      <span className="ml-6 flex items-center">
                        {open ? (
                          <MinusIcon className="h-5 w-5" aria-hidden="true" />
                        ) : (
                          <PlusIcon  className="h-5 w-5" aria-hidden="true" />
                        )}
                      </span>
                    </Disclosure.Button>
                    <Disclosure.Panel className="pt-6">
                      <div className="space-y-6">
                        {
                            pricespiedras && pricespiedras.map((price, index) => {
                                if (price.id === 0) {
                                    return (
                                        <div key={index} className='form-check'>
                                            <input
                                                onChange={e => onChange(e)}
                                                value={price.name}
                                                name='price_range'
                                                type='radio'
                                                className='focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded-full'
                                                defaultChecked
                                            />
                                            <label className='ml-3 min-w-0 flex-1 text-gray-500 font-sofiapro-light'>{price.name}</label>
                                        </div>
                                    )
                                } else {
                                    return (
                                        <div key={index} className='form-check'>
                                            <input
                                                onChange={e => onChange(e)}
                                                value={price.name}
                                                name='price_range'
                                                type='radio'
                                                className='focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded-full'
                                            />
                                            <label className='ml-3 min-w-0 flex-1 text-gray-500 font-sofiapro-light'>{price.name}</label>
                                        </div>
                                    )
                                }
                            })
                        }
                      </div>
                    </Disclosure.Panel>

                    

                  </h3>
                  </>
                )}
                </Disclosure>

                <Disclosure as="div" className="border-t border-gray-200 px-4 py-6">
                {({ open }) => (
                  <>
                  <h3 className="-mx-2 -my-3 flow-root">
                    <Disclosure.Button className="px-2 py-3 bg-white w-full flex items-center justify-between text-gray-400 hover:text-gray-500">
                      <span className="font-sofiapro-regular text-gray-900">Mas Filtros</span>
                      <span className="ml-6 flex items-center">
                        {open ? (
                          <MinusIcon className="h-5 w-5" aria-hidden="true" />
                        ) : (
                          <PlusIcon  className="h-5 w-5" aria-hidden="true" />
                        )}
                      </span>
                    </Disclosure.Button>
                    <Disclosure.Panel className="pt-6">
                      <div className="space-y-6">
                        <div className='form-group '>
                            <label htmlFor='sortBy' className='mr-3 min-w-0 flex-1 text-gray-500'
                            >Ver por</label>
                              <select
                                  className='my-2 font-sofiapro-light inline-flex justify-center w-full rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-100 focus:ring-blue-500'
                                  id='sortBy'
                                  name='sortBy'
                                  onChange={e => onChange(e)}
                                  value={sortBy}
                              >
                                <option value='date_created'>Fecha</option>
                                <option value='price'>Precio</option>
                                <option value='title'>Nombre</option>

                              </select>
                        </div>
                        <div className='form-group'>
                            <label htmlFor='order' className='mr-3 min-w-0 flex-1 text-gray-500'
                            >Orden</label>
                            <select
                                className='my-2 font-sofiapro-light inline-flex justify-center w-full rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-100 focus:ring-blue-500'
                                id='order'
                                name='order'
                                onChange={e => onChange(e)}
                                value={order}
                            >
                                <option value='asc'>A - Z</option>
                                <option value='desc'>Z - A</option>
                            </select>
                        </div>
                      </div>
                    </Disclosure.Panel>
                  </h3>
                  </>
                )}
                </Disclosure>

                <button
                  type="submit"
                  className="inline-flex items-center px-10 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-gray-600 hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
                >
                  Buscar
                </button>
              </form>
            </div>
          </Transition.Child>
        </Dialog>
      </Transition.Root>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="relative z-10 flex items-baseline justify-between pt-8 pb-6 border-b border-gray-200">
          <h1 className="text-4xl font-extrabold tracking-tight text-gray-900">piedras</h1>

          <div className="flex items-center">
            <button
              type="button"
              className="p-2 -m-2 ml-4 sm:ml-6 text-gray-400 hover:text-gray-500 lg:hidden"
              onClick={() => setMobileFiltersOpen(true)}
            >
              <span className="sr-only">Filters</span>
              <FunnelIcon className="w-5 h-5" aria-hidden="true" />
            </button>
          </div>
        </div>

        <section aria-labelledby="products-heading" className="pt-6 pb-24">
          <h2 id="products-heading" className="sr-only">
            piedras
          </h2>

          <div className="grid grid-cols-1 lg:grid-cols-4 gap-x-8 gap-y-10">
            {/* Filters */}
            <form onSubmit={e=>onSubmit(e)} className="hidden lg:block">
              <h2 className='ml-4' >Categorias</h2>
              <hr/>
              <ul role="list" className=" border-l ml-2 text-sm font-medium text-gray-900 space-y-4 pb-6 border-b border-gray-200">
              <div  className='ml-2 flex items-center h-5 my-5'>
                  
                      <input
                        onChange={e => onChange(e)}
                        value={0}
                        name='category_id'
                        type='radio'
                        className='focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded-full'
                        />
                      <label className="ml-2 min-w-0 flex-1 text-gray-500">
                        todo
                      </label>
                          </div>
              {
                      categories_piedras &&
                      categories_piedras !== null &&
                      categories_piedras !== undefined &&
                      categories_piedras.map(category => {
                          if (category.sub_categories.length === 0){
                              return (
                                <>
                                <hr/>
                                  <div key={category.id} className='ml-2 flex items-center h-5 my-5'>
                                      <input
                                          onChange={e => onChange(e)}
                                          value={category.id.toString()}
                                          name='category_id'
                                          type='radio'
                                          className='focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded-full'
                                      />
                                      <label className="ml-2 min-w-0 flex-1 text-gray-500">
                                          {category.name}
                                      </label>
                                  </div>
                                  </>
                              )
                          } else {
                              let result = []
                              result.push(
                                <>
                                <hr/>
                                  <div key={category.id} className='ml-2 flex items-center my-5 h-5'>
                                      <input
                                          onChange={e => onChange(e)}
                                          value={category.id.toString()}
                                          name='category_id'
                                          type='radio'
                                          className='focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded-full'
                                      />
                                      <label className="ml-2 min-w-0 flex-1 text-gray-500">
                                          {category.name}
                                      </label>
                                  </div>
                                  <hr/>
                                  </>
                              )

                              category.sub_categories.map(sub_category => {
                                  result.push(
                                      <div key={sub_category.id} className='ml-3 flex items-center h-5 ml-2 my-5'>
                                          <input
                                              onChange={e => onChange(e)}
                                              value={sub_category.id.toString()}
                                              name='category_id'
                                              type='radio'
                                              className='focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded-full'
                                          />
                                          <label className="ml-2 min-w-0 flex-1 text-gray-500">
                                              {sub_category.name}
                                          </label>
                                      </div>
                                  )
                              })

                              return result
                          }
                      })
                  }
              </ul>

              <Disclosure as="div" className="border-t border-gray-200 px-4 py-6">
                {({ open }) => (
                  <>
                  <h3 className="-mx-2 -my-3 flow-root">
                    <Disclosure.Button className="px-2 py-3 bg-white w-full flex items-center justify-between text-gray-400 hover:text-gray-500">
                      <span className="font-sofiapro-regular text-gray-900">Precios</span>
                      <span className="ml-6 flex items-center">
                        {open ? (
                          <MinusIcon className="h-5 w-5" aria-hidden="true" />
                        ) : (
                          <PlusIcon  className="h-5 w-5" aria-hidden="true" />
                        )}
                      </span>
                    </Disclosure.Button>
                    <Disclosure.Panel className="pt-6">
                      <div className="space-y-6">
                        {
                            pricespiedras && pricespiedras.map((price, index) => {
                                if (price.id === 0) {
                                    return (
                                        <div key={index} className='form-check'>
                                            <input
                                                onChange={e => onChange(e)}
                                                value={price.name}
                                                name='price_range'
                                                type='radio'
                                                className='focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded-full'
                                                defaultChecked
                                            />
                                            <label className='ml-3 min-w-0 flex-1 text-gray-500 font-sofiapro-light'>{price.name}</label>
                                        </div>
                                    )
                                } else {
                                    return (
                                        <div key={index} className='form-check'>
                                            <input
                                                onChange={e => onChange(e)}
                                                value={price.name}
                                                name='price_range'
                                                type='radio'
                                                className='focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded-full'
                                            />
                                            <label className='ml-3 min-w-0 flex-1 text-gray-500 font-sofiapro-light'>{price.name}</label>
                                        </div>
                                    )
                                }
                            })
                        }
                      </div>
                    </Disclosure.Panel>

                    

                  </h3>
                  </>
                )}
                </Disclosure>

                <Disclosure as="div" className="border-t border-gray-200 px-4 py-6">
                {({ open }) => (
                  <>
                  <h3 className="-mx-2 -my-3 flow-root">
                    <Disclosure.Button className="px-2 py-3 bg-white w-full flex items-center justify-between text-gray-400 hover:text-gray-500">
                      <span className="font-sofiapro-regular text-gray-900">Mas Filtros</span>
                      <span className="ml-6 flex items-center">
                        {open ? (
                          <MinusIcon className="h-5 w-5" aria-hidden="true" />
                        ) : (
                          <PlusIcon  className="h-5 w-5" aria-hidden="true" />
                        )}
                      </span>
                    </Disclosure.Button>
                    <Disclosure.Panel className="pt-6">
                      <div className="space-y-6">
                        <div className='form-group '>
                            <label htmlFor='sortBy' className='mr-3 min-w-0 flex-1 text-gray-500'
                            >Ver por</label>
                              <select
                                  className='my-2 font-sofiapro-light inline-flex justify-center w-full rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-100 focus:ring-blue-500'
                                  id='sortBy'
                                  name='sortBy'
                                  onChange={e => onChange(e)}
                                  value={sortBy}
                              >
                                <option value='date_created'>Fecha</option>
                                <option value='price'>Precio</option>
                                <option value='title'>Nombre</option>

                              </select>
                        </div>
                        <div className='form-group'>
                            <label htmlFor='order' className='mr-3 min-w-0 flex-1 text-gray-500'
                            >Orden</label>
                            <select
                                className='my-2 font-sofiapro-light inline-flex justify-center w-full rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-100 focus:ring-blue-500'
                                id='order'
                                name='order'
                                onChange={e => onChange(e)}
                                value={order}
                            >
                                <option value='asc'>A - Z</option>
                                <option value='desc'>Z - A</option>
                            </select>
                        </div>
                      </div>
                    </Disclosure.Panel>
                  </h3>
                  </>
                )}
                </Disclosure>

                <button
                  type="submit"
                  className="float-right inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-gray-600 hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
                >
                  Buscar
                </button>
            </form>

            {/* Product grid */}
            <div className="col-span-3">
              {/* Replace with your content */}

              {piedras && showProducts()}

            </div>
          </div>
        </section>
      </main>
    </div>
  </div>
      </Layout>
  </>
    
  )
}
const mapStateToProps = state => ({
    categories: state.Categories.categories,
    piedras: state.Piedras.piedras,
    filtered_piedras: state.Piedras.filtered_piedras,
    categories_piedras: state.Categories.categories_piedras
    
  })
  
export default connect(mapStateToProps, {get_categories, get_categories_piedras, get_piedras, get_filtered_piedras}) (Piedras)
