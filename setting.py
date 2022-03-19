from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider

def cassandra_connect():
    cloud_config= {
        'secure_connect_bundle': 'secure-connect-internship.zip'
}
    auth_provider = PlainTextAuthProvider('XMABSQwdhzHFcBgMusEhugoq', 'P9pT00CD8yfspKQRxTphadR5HWX+8HD7eQ3KCk87hy9fE.npscN4_wbO5+H2Ki1RllpBQ0z3Q_FBu2TbW7Fdxuw-knIgnulu5s9yv-+U9GX,67ewGCuR6AFws.ZT,bTq')
    cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
    session = cluster.connect('icecream')
    return session
