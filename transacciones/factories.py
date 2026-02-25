class ContratoFactory:
    @staticmethod
    def crear_arriendo(solicitud):
        return Contrato.objects.create(
            tipo='arriendo',
            propiedad=solicitud.propiedad,
            inquilino=solicitud.solicitante,
            propietario=solicitud.propiedad.propietario,
            fecha_inicio=solicitud.fecha_inicio_deseada,
            fecha_fin=solicitud.fecha_fin_deseada,
            valor_mensual=solicitud.propiedad.precio,
            estado='pendiente_firma'
        )
    
    @staticmethod
    def crear_venta(oferta):
        return Contrato.objects.create(
            tipo='venta',
            propiedad=oferta.propiedad,
            comprador=oferta.comprador,
            propietario=oferta.propiedad.propietario,
            valor_total=oferta.valor_oferta,
            estado='pendiente_firma'
        )