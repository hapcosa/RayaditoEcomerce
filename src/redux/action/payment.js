import axios from 'axios';
import { setAlert } from './alert';

import {
    GET_PAYMENT_TOTAL_SUCCESS,
    GET_PAYMENT_TOTAL_FAIL,
    LOAD_BT_TOKEN_SUCCESS,
    LOAD_BT_TOKEN_FAIL,
    PAYMENT_SUCCESS,
    PAYMENT_FAIL,
    RESET_PAYMENT_INFO,
    SET_PAYMENT_LOADING,
    REMOVE_PAYMENT_LOADING,
    STATUS_PAYMENT_SUCCESS,
    STATUS_PAYMENT_REJECTED,
    EMPTY_CART,

} from './types';


export const get_payment_total = (shipping_id, coupon_name) => async dispatch => {
    const config = {
        headers: {
            'Accept': 'application/json',
            'Authorization': `JWT ${localStorage.getItem('access')}`
        }
    };

    try {
        const res = await axios.get(`${import.meta.env.VITE_API_URL}/api/payment/get-payment-total?shipping_id=${shipping_id}&coupon_name=${coupon_name}`, config);

        if (res.status === 200 && !res.data.error) {
            dispatch({
                type: GET_PAYMENT_TOTAL_SUCCESS,
                payload: res.data
            });
        } else {
            dispatch({
                type: GET_PAYMENT_TOTAL_FAIL
            });
        }
    } catch(err) {
        dispatch({
            type: GET_PAYMENT_TOTAL_FAIL
        });
    }
}

export const get_client_token = () => async dispatch => {
    const config = {
        headers: {
            'Accept': 'application/json',
            'Authorization': `JWT ${localStorage.getItem('access')}`
        }
    };

    try {
        const res = await axios.get(`${import.meta.env.VITE_API_URL}/api/payment/get-token`, config);

        if (res.status === 200) {
            dispatch({
                type: LOAD_BT_TOKEN_SUCCESS,
                payload: res.data
            });
        } else {
            dispatch({
                type: LOAD_BT_TOKEN_FAIL
            });
        }
    } catch(err) {
        dispatch({
            type: LOAD_BT_TOKEN_FAIL
        });
    }
}

export const process_payment = (
    email,
    shipping_id,
    first_name,
    last_name,
    address_line_1,
    city,
    state_province_region,
    postal_zip_code,
    telephone_number,
    items,

) => async dispatch => {

    const config = {
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
    }
    //config['headers']['Authorization'] = `JWT ${localStorage.getItem('access')}`
    const body = JSON.stringify({
        email,
        shipping_id,
        first_name,
        last_name,
        address_line_1,
        city,
        state_province_region,
        postal_zip_code,
        telephone_number,
        items,
    });

    dispatch({
        type: SET_PAYMENT_LOADING
    });

    try {
        const res = await axios.post(`${import.meta.env.VITE_API_URL}/api/payment/make-payment`, body, config);
        if (res.status === 200) {
            dispatch({
                type: PAYMENT_SUCCESS,
                payload: res.data
            });
        
            dispatch(setAlert("redirigiendo a mercado pago", 'green'));
        } else {
            dispatch({
                type: PAYMENT_FAIL
            });
            dispatch(setAlert("mal", 'red'));
        }
    } catch(err) {
        dispatch({
            type: PAYMENT_FAIL
        });
        dispatch(setAlert('Error procesando el pago' + err, 'red'));
    }

    dispatch({
        type: REMOVE_PAYMENT_LOADING
    });
    window.scrollTo(0, 0);
}
export const reset = () => dispatch => {
    dispatch({
        type: RESET_PAYMENT_INFO
    });
};
export const process_payment_auth = (
    shipping_id,
    profile_id,
    items, loading

) => async dispatch => {

    const config = {
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': `JWT ${localStorage.getItem('access')}`,
        }
    }
    if(!loading){
        const body = JSON.stringify({
            shipping_id,
            profile_id,
            items,
        });
    
        dispatch({
            type: SET_PAYMENT_LOADING
        });
    
        try {
            console.log(body)
            const res = await axios.post(`${import.meta.env.VITE_API_URL}/api/payment/make-payment`, body, config);
            if (res.status === 200) {
    
                dispatch({
                    type: PAYMENT_SUCCESS,
                    payload: res.data
                });
                dispatch(setAlert("redirigiendo a mercado pago", 'green'))
            } else {
                dispatch({
                    type: PAYMENT_FAIL
                });
                dispatch(setAlert("mal", 'red'));
            }
        } catch(err) {
            dispatch({
                type: PAYMENT_FAIL
            });
            dispatch(setAlert('Error procesando el pago' + err, 'red'));
        }
    
        dispatch({
            type: REMOVE_PAYMENT_LOADING
        });
        window.scrollTo(0, 0);
    }
    console.log('no hacer nada')
   
}

export const process_repayment_auth =(orderId) => async dispatch => {

    const config = {
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': `JWT ${localStorage.getItem('access')}`,
        }
    }
    //config['headers']['Authorization'] = `JWT ${localStorage.getItem('access')}`
    const body = JSON.stringify({
        orderId
    });

    dispatch({
        type: SET_PAYMENT_LOADING
    });

    try {
        console.log(body)
        const res = await axios.post(`${import.meta.env.VITE_API_URL}/api/payment/make-payment`, body, config);
        if (res.status === 200) {

            dispatch({
                type: PAYMENT_SUCCESS,
                payload: res.data
            });
            dispatch(setAlert("redirigiendo a mercado pago", 'green'))
        } else {
            dispatch({
                type: PAYMENT_FAIL
            });
            dispatch(setAlert("mal", 'red'));
        }
    } catch(err) {
        dispatch({
            type: PAYMENT_FAIL
        });
        dispatch(setAlert('Error procesando el pago' + err, 'red'));
    }

    dispatch({
        type: REMOVE_PAYMENT_LOADING
    });
    window.scrollTo(0, 0);
}


export const statuspayment = (paymentId, orderId) =>  async dispatch => {
    const config = {
        headers: {
            'Accept': 'application/json',
            'Authorization': `JWT ${localStorage.getItem('access')}`,
        }
    }
    //config['headers']['Authorization'] = `JWT ${localStorage.getItem('access')}`
    try {
        const params = new URLSearchParams();
        if (paymentId) {
            params.append('payment_id', paymentId);
        } else if (orderId) {
            params.append('order_id', orderId);
        }
        const res = await axios.get(`${import.meta.env.VITE_API_URL}/api/payment/status-payment/?${params.toString()}`,  config);
        if (res.status === 200) {
            dispatch({
                type: STATUS_PAYMENT_SUCCESS,
                payload: res.data
            })
            if (res.data.payment_status === 'approved' || res.data.order_status === 'procesado') {
                localStorage.removeItem('cart');
                dispatch({
                    type: EMPTY_CART,
                });
            }
        }else{
            dispatch({
                type: STATUS_PAYMENT_REJECTED,
                payload: res.data
            })
            
        }
    }
    catch(err){
        dispatch({
            type: STATUS_PAYMENT_REJECTED,
            payload: { payment_status: 'unknown', order_status: null }
        });
        dispatch(setAlert('Error de servidor:' + err, 'red'));
    }
};
