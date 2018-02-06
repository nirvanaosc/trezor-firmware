from trezor import wire


async def sign_tx(ctx, msg):
    from trezor.messages.RequestType import TXFINISHED
    from trezor.messages.wire_types import TxAck

    from apps.common import seed
    from . import signing
    from . import layout

    # TODO: rework this so we don't have to pass root to signing.sign_tx
    root = await seed.derive_node(ctx, [])

    signer = signing.sign_tx(msg, root)
    res = None
    while True:
        try:
            req = signer.send(res)
        except signing.SigningError as e:
            raise wire.FailureError(*e.args)
        except signing.AddressError as e:
            raise wire.FailureError(*e.args)
        if req.__qualname__ == 'TxRequest':
            if req.request_type == TXFINISHED:
                break
            res = await ctx.call(req, TxAck)
        elif req.__qualname__ == 'UiConfirmOutput':
            res = await layout.confirm_output(ctx, req.output, req.coin)
        elif req.__qualname__ == 'UiConfirmTotal':
            res = await layout.confirm_total(ctx, req.spending, req.fee, req.coin)
        elif req.__qualname__ == 'UiConfirmFeeOverThreshold':
            res = await layout.confirm_feeoverthreshold(ctx, req.fee, req.coin)
        else:
            raise TypeError('Invalid signing instruction')
    return req
