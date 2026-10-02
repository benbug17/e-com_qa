@bdd
Feature: Checkout
  As a shopper I want to buy products so that I receive an order confirmation

  @smoke
  Scenario: Successful checkout of a single product
    Given I am logged in as "qa_user"
    When I add product 3 to my cart
    And I checkout
    Then I see an order confirmation
    And the order exists in the database with total 25.00

  @negative
  Scenario: Checkout with an empty cart is rejected
    Given I am logged in as "qa_user"
    When I checkout
    Then I see the error "empty"

  @negative
  Scenario: Login with a wrong password is rejected
    Given I am on the login page
    When I login as "qa_user" with password "wrong"
    Then I see the error "Invalid username or password"
