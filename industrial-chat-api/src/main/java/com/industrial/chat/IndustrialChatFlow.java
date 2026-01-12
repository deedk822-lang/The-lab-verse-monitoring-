package com.industrial.chat;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.document.Document;
import org.springframework.ai.vectorstore.SearchRequest;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.integration.dsl.IntegrationFlow;
import org.springframework.integration.http.dsl.Http;

import java.util.List;
import java.util.stream.Collectors;

@Configuration
public class IndustrialChatFlow {

    @Bean
    public IntegrationFlow floatingWindowFlow(ChatClient.Builder chatClientBuilder, VectorStore vectorStore) {

        // 1. Define the Chat Client with default "Expert" persona
        ChatClient chatClient = chatClientBuilder
                .defaultSystem("You are an industrial support assistant named Airo. Answer strictly based on the provided technical manuals.")
                .build();

        return IntegrationFlow.from(Http.inboundGateway("/api/chat")
                .requestMapping(m -> m.methods(HttpMethod.POST))
                .crossOrigin(cors -> cors.origin("*")) // Allow Global Footer access
                .requestPayloadType(String.class))

            // 2. "Enrich" the user's question with data from the Vault
            .handle((payload, headers) -> {
                String userQuestion = (String) payload;

                // Search for the 3 most relevant pages in your PDF manuals
                List<Document> similarDocs = vectorStore.similaritySearch(
                    SearchRequest.query(userQuestion).withTopK(3)
                );

                String manualContext = similarDocs.stream()
                    .map(Document::getContent)
                    .collect(Collectors.joining("\n\n"));

                // 3. Send the Combined Prompt to the AI
                return chatClient.prompt()
                    .user(u -> u.text("Context:\n{context}\n\nQuestion:\n{question}")
                        .param("context", manualContext)
                        .param("question", userQuestion))
                    .call()
                    .content();
            })
            .get();
    }
}
