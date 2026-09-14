package com.talan.gatewayservice.config;

import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationToken;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.util.stream.Collectors;

@Component
public class UserHeaderGlobalFilter implements GlobalFilter, Ordered {

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        System.out.println("🔍 [FILTRE] Requête reçue : " + exchange.getRequest().getPath());

        return exchange.getPrincipal()
                .cast(JwtAuthenticationToken.class)
                .map(auth -> {
                    String username = auth.getToken().getClaimAsString("preferred_username");
                    String roles = auth.getAuthorities().stream()
                            .map(a -> a.getAuthority().replace("ROLE_", ""))
                            .collect(Collectors.joining(","));

                    System.out.println("🔍 [FILTRE] Utilisateur trouvé : " + username + " | Rôles : " + roles);

                    ServerHttpRequest mutatedRequest = exchange.getRequest().mutate()
                            .header("X-User", username != null ? username : "inconnu")
                            .header("X-User-Roles", roles)
                            .build();

                    return exchange.mutate().request(mutatedRequest).build();
                })
                .switchIfEmpty(Mono.fromRunnable(() ->
                        System.out.println("⚠️ [FILTRE] Aucun principal JWT trouvé sur cette requête !")
                ))
                .defaultIfEmpty(exchange)
                .flatMap(chain::filter);
    }

    @Override
    public int getOrder() {
        return Ordered.LOWEST_PRECEDENCE;
    }
}