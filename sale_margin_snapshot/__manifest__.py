{
    'name': 'Sale Margin Snapshot',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Congela el costo del producto en la línea de venta para reportes históricos.',
    'author': "Sergio Alberto Perez Plata",
    'depends': ['sale', 'product', 'base'], 
    'data': [
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}