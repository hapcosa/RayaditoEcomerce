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
    STATUS_PAYMENT_REJECTED,
    STATUS_PAYMENT_SUCCESS,
    STATUS_PAYMENT_CANCELED,
} from '../action/types';


const initialState = {
    made_payment: false,
    original_price: 0.0,
    total_amount: 0.0,
    loading: false,
    error: null,
    url: null,
    status: null,
    order_status: null,
    order_id: null,
    transaction_id: null
};

export default function Payment(state = initialState, action) {
    const { type, payload } = action;

    switch(type) {
        case GET_PAYMENT_TOTAL_SUCCESS:
            return {
                ...state,
            }
        case GET_PAYMENT_TOTAL_FAIL:
            return {
                ...state,
                original_price: 0.00,
                total_amount: 0.00,
                url: null

            }
        case PAYMENT_SUCCESS:
            return {
                ...state,
                made_payment: true,
                url: payload.response.init_point,
                order_id: payload.order_id,
            }
        case PAYMENT_FAIL:
            return {
                ...state,
                made_payment: false,
                url: null,
                order_id: null,

            }
        case SET_PAYMENT_LOADING:
            return {
                ...state,
                loading: true
            }
        case REMOVE_PAYMENT_LOADING:
            return {
                ...state,
                loading: false
            }
        case STATUS_PAYMENT_SUCCESS:
            return {
                ...state,
                status: payload.payment_status || payload.order_status,
                order_status: payload.order_status,
                order_id: payload.order_id,
                transaction_id: payload.transaction_id,
            }
        case STATUS_PAYMENT_REJECTED:
             return {
                ...state,
                 status: payload.payment_status || payload.order_status || 'unknown',
                 order_status: payload.order_status || null,
                 order_id: payload.order_id || null,
                 transaction_id: payload.transaction_id || null,
            }

        case RESET_PAYMENT_INFO:
            return {
                ...state,
                made_payment: false,
                original_price: 0.0,
                total_amount: 0.0,
                loading: false,
                error: null,
                url: null,
                status: null,
                order_status: null,
                order_id: null,
                transaction_id: null,
            }
        default:
            return state;
    }
}
