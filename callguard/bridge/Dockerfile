FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /src
COPY pom.xml .
COPY src ./src
RUN mvn -q -DskipTests package
FROM eclipse-temurin:17-jre
COPY --from=build /src/target/bridge.jar /bridge.jar
EXPOSE 8081
CMD ["java","-jar","/bridge.jar"]
