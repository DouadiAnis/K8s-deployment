FROM nginx:alpine
# On supprime la config par défaut
RUN rm /etc/nginx/conf.d/default.conf
# On ajoute la nôtre
COPY default.conf /etc/nginx/conf.d/
# On ajoute le code HTML
COPY index.html /usr/share/nginx/html/