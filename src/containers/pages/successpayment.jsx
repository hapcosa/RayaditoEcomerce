import { useEffect } from 'react';
import { connect } from 'react-redux';
import { useNavigate, useSearchParams } from 'react-router-dom';

import Layout from '../../hocs/layout/layout';
import { statuspayment } from '../../redux/action/payment';

const paymentCopy = {
    approved: {
        title: 'Pago aprobado',
        text: 'Recibimos la confirmación de Mercado Pago. Puedes revisar el detalle en tus pedidos.',
        tone: 'text-green-900',
        button: 'Ver mis pedidos',
        route: '/dashboard/payments',
    },
    rejected: {
        title: 'Pago rechazado',
        text: 'Mercado Pago rechazó la operación. Puedes volver al checkout e intentar con otro medio de pago.',
        tone: 'text-red-900',
        button: 'Volver al checkout',
        route: '/checkout',
    },
    cancelled: {
        title: 'Pago cancelado',
        text: 'La operación fue cancelada. Tu pedido sigue pendiente hasta completar el pago.',
        tone: 'text-gray-900',
        button: 'Volver al checkout',
        route: '/checkout',
    },
    pending: {
        title: 'Pago pendiente',
        text: 'Mercado Pago todavía está procesando la operación. Actualizaremos el pedido cuando llegue el webhook.',
        tone: 'text-yellow-900',
        button: 'Ver mis pedidos',
        route: '/dashboard/payments',
    },
    unknown: {
        title: 'Estamos revisando tu pago',
        text: 'No pudimos confirmar el estado final todavía. Revisa tus pedidos en unos minutos.',
        tone: 'text-gray-900',
        button: 'Ir al inicio',
        route: '/',
    },
};

const normalizeStatus = (paymentState, orderStatus, statusParam) => {
    if (paymentState === 'approved' || orderStatus === 'procesado' || statusParam === 'approved') {
        return 'approved';
    }
    if (
        paymentState === 'rejected'
        || orderStatus === 'rechazado'
        || statusParam === 'rejected'
        || statusParam === 'failure'
    ) {
        return 'rejected';
    }
    if (
        paymentState === 'cancelled'
        || paymentState === 'refunded'
        || paymentState === 'charged_back'
        || orderStatus === 'cancelado'
        || statusParam === 'cancelled'
    ) {
        return 'cancelled';
    }
    if (
        paymentState === 'pending'
        || orderStatus === 'no procesado'
        || statusParam === 'pending'
        || statusParam === 'in_process'
    ) {
        return 'pending';
    }
    return 'unknown';
};

const Success = ({
    statuspayment,
    payment_state,
    order_status,
    transaction_id,
}) => {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const paymentId = searchParams.get('payment_id');
    const orderId = searchParams.get('external_reference') || searchParams.get('order_id');
    const statusParam = searchParams.get('status');
    const displayStatus = normalizeStatus(payment_state, order_status, statusParam);
    const copy = paymentCopy[displayStatus];

    useEffect(() => {
        window.scrollTo(0, 0);
        if (paymentId || orderId) {
            statuspayment(paymentId, orderId);
        }
    }, [paymentId, orderId, statuspayment]);

    return (
        <Layout>
            <section className="min-h-screen bg-white px-6 pt-32 pb-20">
                <div className="mx-auto max-w-2xl text-center">
                    <p className={`text-2xl font-semibold ${copy.tone}`}>{copy.title}</p>
                    <p className="mt-4 text-base leading-7 text-gray-600">{copy.text}</p>
                    {orderId && (
                        <p className="mt-4 text-sm text-gray-500">Orden #{orderId}</p>
                    )}
                    {transaction_id && (
                        <p className="mt-1 text-sm text-gray-500">Transacción {transaction_id}</p>
                    )}
                    <button
                        onClick={() => navigate(copy.route)}
                        className="mx-auto mt-8 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-gray-700 hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
                    >
                        {copy.button}
                    </button>
                </div>
            </section>
        </Layout>
    );
};

const mapStateToProps = state => ({
    payment_state: state.Payment.status,
    order_status: state.Payment.order_status,
    transaction_id: state.Payment.transaction_id,
});

export default connect(mapStateToProps, {
    statuspayment,
})(Success);
