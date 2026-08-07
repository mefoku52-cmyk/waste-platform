openapi: 3.1.0
info:
  title: Circular Materials Exchange Platform API
  version: 0.1.0
  summary: Contract-first API for a B2B platform for trading waste, by-products and secondary raw materials
  description: |
    This OpenAPI contract defines the MVP API surface for the Circular Materials Exchange Platform.
    It is derived from the approved product specification, domain model, workflow states,
    application architecture and database schema.

    Design principles:
    - REST resource-oriented API
    - Explicit workflow transition endpoints for controlled state changes
    - JWT bearer authentication
    - Role-based access control enforced server-side
    - Company-scoped authorization for company actors
    - Auditability for all critical transitions
    - Object storage handled through document metadata plus upload intent flow
servers:
  - url: /api/v1
    description: Version 1 API

tags:
  - name: auth
  - name: users
  - name: roles
  - name: companies
  - name: company-memberships
  - name: company-verification-reviews
  - name: materials-taxonomy
  - name: listings
  - name: listing-photos
  - name: listing-compliance-reviews
  - name: inquiries
  - name: negotiations
  - name: negotiation-messages
  - name: reservations
  - name: logistics
  - name: documents
  - name: document-links
  - name: compliance-cases
  - name: notifications
  - name: analytics
  - name: audit
  - name: admin

security:
  - bearerAuth: []

paths:
  /health:
    get:
      tags: [admin]
      summary: Health check
      operationId: getHealth
      security: []
      responses:
        '200':
          description: Service health
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HealthResponse'

  /auth/login:
    post:
      tags: [auth]
      summary: Authenticate user and issue tokens
      operationId: login
      security: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/LoginRequest'
      responses:
        '200':
          description: Login successful
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AuthTokenPairResponse'
        '401':
          $ref: '#/components/responses/UnauthorizedError'

  /auth/refresh:
    post:
      tags: [auth]
      summary: Refresh access token
      operationId: refreshToken
      security: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/RefreshTokenRequest'
      responses:
        '200':
          description: Token refreshed
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AuthTokenPairResponse'
        '401':
          $ref: '#/components/responses/UnauthorizedError'

  /auth/logout:
    post:
      tags: [auth]
      summary: Revoke current session or refresh token
      operationId: logout
      requestBody:
        required: false
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/LogoutRequest'
      responses:
        '204':
          description: Logged out

  /auth/me:
    get:
      tags: [auth]
      summary: Get authenticated user context
      operationId: getCurrentUser
      responses:
        '200':
          description: Authenticated user context
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CurrentUserResponse'

  /users:
    get:
      tags: [users]
      summary: List users
      operationId: listUsers
      parameters:
        - $ref: '#/components/parameters/PageParam'
        - $ref: '#/components/parameters/PageSizeParam'
        - name: status
          in: query
          schema:
            $ref: '#/components/schemas/UserStatus'
        - name: companyId
          in: query
          schema:
            type: string
            format: uuid
        - name: q
          in: query
          schema:
            type: string
      responses:
        '200':
          description: Users list
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedUsersResponse'
    post:
      tags: [users]
      summary: Create user
      operationId: createUser
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserCreateRequest'
      responses:
        '201':
          description: User created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserResponse'
        '409':
          $ref: '#/components/responses/ConflictError'

  /users/{userId}:
    get:
      tags: [users]
      summary: Get user detail
      operationId: getUser
      parameters:
        - $ref: '#/components/parameters/UserIdParam'
      responses:
        '200':
          description: User detail
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserResponse'
        '404':
          $ref: '#/components/responses/NotFoundError'
    patch:
      tags: [users]
      summary: Update user
      operationId: updateUser
      parameters:
        - $ref: '#/components/parameters/UserIdParam'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserUpdateRequest'
      responses:
        '200':
          description: User updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserResponse'

  /users/{userId}/status:
    patch:
      tags: [users]
      summary: Update user status
      operationId: transitionUserStatus
      parameters:
        - $ref: '#/components/parameters/UserIdParam'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserStatusTransitionRequest'
      responses:
        '200':
          description: User status updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserResponse'
        '400':
          $ref: '#/components/responses/InvalidTransitionError'

  /roles:
    get:
      tags: [roles]
      summary: List roles
      operationId: listRoles
      responses:
        '200':
          description: Roles list
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RolesResponse'

  /user-role-assignments:
    get:
      tags: [roles]
      summary: List user role assignments
      operationId: listUserRoleAssignments
      parameters:
        - name: userId
          in: query
          schema:
            type: string
            format: uuid
        - name: roleCode
          in: query
          schema:
            $ref: '#/components/schemas/RoleCode'
        - name: status
          in: query
          schema:
            $ref: '#/components/schemas/UserRoleAssignmentStatus'
      responses:
        '200':
          description: Assignment list
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedUserRoleAssignmentsResponse'
    post:
      tags: [roles]
      summary: Assign role to user
      operationId: createUserRoleAssignment
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserRoleAssignmentCreateRequest'
      responses:
        '201':
          description: Role assignment created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserRoleAssignmentResponse'

  /user-role-assignments/{assignmentId}/revoke:
    post:
      tags: [roles]
      summary: Revoke role assignment
      operationId: revokeUserRoleAssignment
      parameters:
        - $ref: '#/components/parameters/AssignmentIdParam'
      requestBody:
        required: false
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/RevocationRequest'
      responses:
        '200':
          description: Role assignment revoked
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserRoleAssignmentResponse'

  /companies:
    get:
      tags: [companies]
      summary: List companies
      operationId: listCompanies
      parameters:
        - $ref: '#/components/parameters/PageParam'
        - $ref: '#/components/parameters/PageSizeParam'
        - name: status
          in: query
          schema:
            $ref: '#/components/schemas/CompanyStatus'
        - name: companyType
          in: query
          schema:
            $ref: '#/components/schemas/CompanyType'
        - name: sellerCapability
          in: query
          schema:
            type: boolean
        - name: buyerCapability
          in: query
          schema:
            type: boolean
        - name: logisticsCapability
          in: query
          schema:
            type: boolean
        - name: q
          in: query
          schema:
            type: string
      responses:
        '200':
          description: Companies list
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedCompaniesResponse'
    post:
      tags: [companies]
      summary: Create company
      operationId: createCompany
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CompanyCreateRequest'
      responses:
        '201':
          description: Company created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CompanyResponse'

  /companies/{companyId}:
    get:
      tags: [companies]
      summary: Get company detail
      operationId: getCompany
      parameters:
        - $ref: '#/components/parameters/CompanyIdParam'
      responses:
        '200':
          description: Company detail
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CompanyResponse'
    patch:
      tags: [companies]
      summary: Update company
      operationId: updateCompany
      parameters:
        - $ref: '#/components/parameters/CompanyIdParam'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CompanyUpdateRequest'
      responses:
        '200':
          description: Company updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CompanyResponse'

  /companies/{companyId}/memberships:
    get:
      tags: [company-memberships]
      summary: List company memberships
      operationId: listCompanyMemberships
      parameters:
        - $ref: '#/components/parameters/CompanyIdParam'
        - name: status
          in: query
          schema:
            $ref: '#/components/schemas/CompanyMembershipStatus'
      responses:
        '200':
          description: Memberships list
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedCompanyMembershipsResponse'
    post:
      tags: [company-memberships]
      summary: Create company membership
      operationId: createCompanyMembership
      parameters:
        - $ref: '#/components/parameters/CompanyIdParam'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CompanyMembershipCreateRequest'
      responses:
        '201':
          description: Membership created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CompanyMembershipResponse'

  /company-memberships/{membershipId}:
    patch:
      tags: [company-memberships]
      summary: Update company membership
      operationId: updateCompanyMembership
      parameters:
        - $ref: '#/components/parameters/MembershipIdParam'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CompanyMembershipUpdateRequest'
      responses:
        '200':
          description: Membership updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CompanyMembershipResponse'

  /company-memberships/{membershipId}/status:
    patch:
      tags: [company-memberships]
      summary: Update company membership status
      operationId: transitionCompanyMembershipStatus
      parameters:
        - $ref: '#/components/parameters/MembershipIdParam'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CompanyMembershipStatusTransitionRequest'
      responses:
        '200':
          description: Membership status updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CompanyMembershipResponse'

  /company-verification-reviews:
    get:
      tags: [company-verification-reviews]
      summary: List company verification reviews
      operationId: listCompanyVerificationReviews
      parameters:
        - name: companyId
          in: query
          schema:
            type: string
            format: uuid
        - name: status
          in: query
          schema:
            $ref: '#/components/schemas/CompanyVerificationReviewStatus'
        - name: reviewerUserId
          in: query
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Verification reviews list
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedCompanyVerificationReviewsResponse'
    post:
      tags: [company-verification-reviews]
      summary: Submit company verification review request
      operationId: createCompanyVerificationReview
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CompanyVerificationReviewCreateRequest'
      responses:
        '201':
          description: Verification review created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CompanyVerificationReviewResponse'

  /company-verification-reviews/{reviewId}:
    get:
      tags: [company-verification-reviews]
      summary: Get company verification review detail
      operationId: getCompanyVerificationReview
      parameters:
        - $ref: '#/components/parameters/ReviewIdParam'
      responses:
        '200':
          description: Verification review detail
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CompanyVerificationReviewResponse'

  /company-verification-reviews/{reviewId}/status:
    patch:
      tags: [company-verification-reviews]
      summary: Transition company verification review status
      operationId: transitionCompanyVerificationReviewStatus
      parameters:
        - $ref: '#/components/parameters/ReviewIdParam'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CompanyVerificationReviewStatusTransitionRequest'
      responses:
        '200':
          description: Verification review status updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CompanyVerificationReviewResponse'
        '400':
          $ref: '#/components/responses/InvalidTransitionError'

  /material-categories:
    get:
      tags: [materials-taxonomy]
      summary: List material categories
      operationId: listMaterialCategories
      parameters:
        - name: status
          in: query
          schema:
            $ref: '#/components/schemas/TaxonomyStatus'
      responses:
        '200':
          description: Material categories
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MaterialCategoriesResponse'
    post:
      tags: [materials-taxonomy]
      summary: Create material category
      operationId: createMaterialCategory
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MaterialCategoryCreateRequest'
      responses:
        '201':
          description: Material category created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MaterialCategoryResponse'

  /material-categories/{categoryId}:
    get:
      tags: [materials-taxonomy]
      summary: Get material category detail
      operationId: getMaterialCategory
      parameters:
        - $ref: '#/components/parameters/CategoryIdParam'
      responses:
        '200':
          description: Material category detail
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MaterialCategoryResponse'
    patch:
      tags: [materials-taxonomy]
      summary: Update material category
      operationId: updateMaterialCategory
      parameters:
        - $ref: '#/components/parameters/CategoryIdParam'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MaterialCategoryUpdateRequest'
      responses:
        '200':
          description: Material category updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MaterialCategoryResponse'

  /material-subtypes:
    get:
      tags: [materials-taxonomy]
      summary: List material subtypes
      operationId: listMaterialSubtypes
      parameters:
        - name: categoryId
          in: query
          schema:
            type: string
            format: uuid
        - name: status
          in: query
          schema:
            $ref: '#/components/schemas/TaxonomyStatus'
      responses:
        '200':
          description: Material subtypes
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MaterialSubtypesResponse'
    post:
      tags: [materials-taxonomy]
      summary: Create material subtype
      operationId: createMaterialSubtype
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MaterialSubtypeCreateRequest'
      responses:
        '201':
          description: Material subtype created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MaterialSubtypeResponse'

  /material-subtypes/{subtypeId}:
    get:
      tags: [materials-taxonomy]
      summary: Get material subtype detail
      operationId: getMaterialSubtype
      parameters:
        - $ref: '#/components/parameters/SubtypeIdParam'
      responses:
        '200':
          description: Material subtype detail
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MaterialSubtypeResponse'
    patch:
      tags: [materials-taxonomy]
      summary: Update material subtype
      operationId: updateMaterialSubtype
      parameters:
        - $ref: '#/components/parameters/SubtypeIdParam'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MaterialSubtypeUpdateRequest'
      responses:
        '200':
          description: Material subtype updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MaterialSubtypeResponse'

  /listings:
    get:
      tags: [listings]
      summary: List listings
      operationId: listListings
      parameters:
        - $ref: '#/components/parameters/PageParam'
        - $ref: '#/components/parameters/PageSizeParam'
        - name: sellerCompanyId
          in: query
          schema:
            type: string
            format: uuid
        - name: materialCategoryId
          in: query
          schema:
            type: string
            format: uuid
        - name: materialSubtypeId
          in: query
          schema:
            type: string
            format: uuid
        - name: status
          in: query
          schema:
            $ref: '#/components/schemas/ListingStatus'
        - name: unit
          in: query
          schema:
            $ref: '#/components/schemas/UnitCode'
        - name: priceModel
          in: query
          schema:
            $ref: '#/components/schemas/PriceModel'
        - name: quantityMin
          in: query
          schema:
            type: number
        - name: quantityMax
          in: query
          schema:
            type: number
        - name: availableFrom
          in: query
          schema:
            type: string
            format: date
        - name: availableTo
          in: query
          schema:
            type: string
            format: date
        - name: q
          in: query
          schema:
            type: string
        - name: sort
          in: query
          schema:
            type: string
            enum: [created_at_desc, created_at_asc, quantity_desc, quantity_asc, availability_start_date_asc, relevance]
      responses:
        '200':
          description: Listings list
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedListingsResponse'
    post:
      tags: [listings]
      summary: Create listing
      operationId: createListing
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ListingCreateRequest'
      responses:
        '201':
          description: Listing created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ListingResponse'

  /listings/{listingId}:
    get:
      tags: [listings]
      summary: Get listing detail
      operationId: getListing
      parameters:
        - $ref: '#/components/parameters/ListingIdParam'
      responses:
        '200':
          description: Listing detail
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ListingResponse'
    patch:
      tags: [listings]
      summary: Update listing
      operationId: updateListing
      parameters:
        - $ref: '#/components/parameters/ListingIdParam'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ListingUpdateRequest'
      responses:
        '200':
          description: Listing updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ListingResponse'

  /listings/{listingId}/status:
    patch:
      tags: [listings]
      summary: Transition listing status
      operationId: transitionListingStatus
      parameters:
        - $ref: '#/components/parameters/ListingIdParam'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ListingStatusTransitionRequest'
      responses:
        '200':
          description: Listing status updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ListingResponse'
        '400':
          $ref: '#/components/responses/InvalidTransitionError'

  /listings/{listingId}/available-transitions:
    get:
      tags: [listings]
      summary: Get listing transitions allowed for current user
      operationId: getListingAvailableTransitions
      parameters:
        - $ref: '#/components/parameters/ListingIdParam'
      responses:
        '200':
          description: Allowed transitions
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AvailableTransitionsResponse'

  /listings/{listingId}/photos:
    get:
      tags: [listing-photos]
      summary: List listing photos
      operationId: listListingPhotos
      parameters:
        - $ref: '#/components/parameters/ListingIdParam'
      responses:
        '200':
          description: Listing photos
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ListingPhotosResponse'
    post:
      tags: [listing-photos]
      summary: Attach photo to listing
      operationId: createListingPhoto
      parameters:
        - $ref: '#/components/parameters/ListingIdParam'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ListingPhotoCreateRequest'
      responses:
        '201':
          description: Listing photo created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ListingPhotoResponse'

  /listing-photos/{listingPhotoId}:
    patch:
      tags: [listing-photos]
      summary: Update listing photo metadata
      operationId: updateListingPhoto
      parameters:
        - $ref: '#/components/parameters/ListingPhotoIdParam'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ListingPhotoUpdateRequest'
      responses:
        '200':
          description: Listing photo updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ListingPhotoResponse'

  /listing-compliance-reviews:
    get:
      tags: [listing-compliance-reviews]
      summary: List listing compliance reviews
      operationId: listListingComplianceReviews
      parameters:
        - name: listingId
          in: query
          schema:
            type: string
            format: uuid
        - name: status
          in: query
          schema:
            $ref: '#/components/schemas/ListingComplianceReviewStatus'
        - name: reviewerUserId
          in: query
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Listing compliance reviews
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedListingComplianceReviewsResponse'
    post:
      tags: [listing-compliance-reviews]
      summary: Submit listing compliance review request
      operationId: createListingComplianceReview
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ListingComplianceReviewCreateRequest'
      responses:
        '201':
          description: Listing compliance review created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ListingComplianceReviewResponse'

  /listing-compliance-reviews/{reviewId}:
    get:
      tags: [listing-compliance-reviews]
      summary: Get listing compliance review detail
      operationId: getListingComplianceReview
      parameters:
        - $ref: '#/components/parameters/ReviewIdParam'
      responses:
        '200':
          description: Listing compliance review detail
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ListingComplianceReviewResponse'

  /listing-compliance-reviews/{reviewId}/status:
    patch:
      tags: [listing-compliance-reviews]
      summary: Transition listing compliance review status
      operationId: transitionListingComplianceReviewStatus
      parameters:
        - $ref: '#/components/parameters/ReviewIdParam'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ListingComplianceReviewStatusTransitionRequest'
      responses:
        '200':
          description: Listing compliance review status updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ListingComplianceReviewResponse'
        '400':
          $ref: '#/components/responses/InvalidTransitionError'

  /inquiries:
    get:
      tags: [inquiries]
      summary: List inquiries
      operationId: listInquiries
      parameters:
        - $ref: '#/components/parameters/PageParam'
        - $ref: '#/components/parameters/PageSizeParam'
        - name: listingId
          in: query
          schema:
            type: string
            format: uuid
        - name: buyerCompanyId
          in: query
          schema:
            type: string
            format: uuid
        - name: buyerContactUserId
          in: query
          schema:
            type: string
            format: uuid
        - name: status
          in: query
          schema:
            $ref: '#/components/schemas/InquiryStatus'
      responses:
        '200':
          description: Inquiries list
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedInquiriesResponse'
    post:
      tags: [inquiries]
      summary: Create inquiry
      operationId: createInquiry
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/InquiryCreateRequest'
      responses:
        '201':
          description: Inquiry created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/InquiryResponse'

  /inquiries/{inquiryId}:
    get:
      tags: [inquiries]
      summary: Get inquiry detail
      operationId: getInquiry
      parameters:
        - $ref: '#/components/parameters/InquiryIdParam'
      responses:
        '200':
          description: Inquiry detail
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/InquiryResponse'
    patch:
      tags: [inquiries]
      summary: Update inquiry
      operationId: updateInquiry
      parameters:
        - $ref: '#/components/parameters/InquiryIdParam'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/InquiryUpdateRequest'
      responses:
        '200':
          description: Inquiry updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/InquiryResponse'

  /inquiries/{inquiryId}/status:
    patch:
      tags: [inquiries]
      summary: Transition inquiry status
      operationId: transitionInquiryStatus
      parameters:
        - $ref: '#/components/parameters/InquiryIdParam'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/InquiryStatusTransitionRequest'
      responses:
        '200':
          description: Inquiry status updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/InquiryResponse'
        '400':
          $ref: '#/components/responses/InvalidTransitionError'

  /inquiries/{inquiryId}/available-transitions:
    get:
      tags: [inquiries]
      summary: Get inquiry transitions allowed for current user
      operationId: getInquiryAvailableTransitions
      parameters:
        - $ref: '#/components/parameters/InquiryIdParam'
      responses:
        '200':
          description: Allowed transitions
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AvailableTransitionsResponse'

  /negotiations:
    get:
      tags: [negotiations]
      summary: List negotiations
      operationId: listNegotiations
      parameters:
        - $ref: '#/components/parameters/PageParam'
        - $ref: '#/components/parameters/PageSizeParam'
        - name: inquiryId
          in: query
          schema:
            type: string
            format: uuid
        - name: listingId
          in: query
          schema:
            type: string
            format: uuid
        - name: sellerCompanyId
          in: query
          schema:
            type: string
            format: uuid
        - name: buyerCompanyId
          in: query
          schema:
            type: string
            format: uuid
        - name: status
          in: query
          schema:
            $ref: '#/components/schemas/NegotiationStatus'
      responses:
        '200':
          description: Negotiations list
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedNegotiationsResponse'
    post:
      tags: [negotiations]
      summary: Create negotiation
      operationId: createNegotiation
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/NegotiationCreateRequest'
      responses:
        '201':
          description: Negotiation created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/NegotiationResponse'

  /negotiations/{negotiationId}:
    get:
      tags: [negotiations]
      summary: Get negotiation detail
      operationId: getNegotiation
      parameters:
        - $ref: '#/components/parameters/NegotiationIdParam'
      responses:
        '200':
          description: Negotiation detail
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/NegotiationResponse'

  /negotiations/{negotiationId}/status:
    patch:
      tags: [negotiations]
      summary: Transition negotiation status
      operationId: transitionNegotiationStatus
      parameters:
        - $ref: '#/components/parameters/NegotiationIdParam'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/NegotiationStatusTransitionRequest'
      responses:
        '200':
          description: Negotiation status updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/NegotiationResponse'
        '400':
          $ref: '#/components/responses/InvalidTransitionError'

  /negotiations/{negotiationId}/available-transitions:
    get:
      tags: [negotiations]
      summary: Get negotiation transitions allowed for current user
      operationId: getNegotiationAvailableTransitions
      parameters:
        - $ref: '#/components/parameters/NegotiationIdParam'
      responses:
        '200':
          description: Allowed transitions
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AvailableTransitionsResponse'

  /negotiations/{negotiationId}/messages:
    get:
      tags: [negotiation-messages]
      summary: List negotiation messages
      operationId: listNegotiationMessages
      parameters:
        - $ref: '#/components/parameters/NegotiationIdParam'
      responses:
        '200':
          description: Negotiation messages
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedNegotiationMessagesResponse'
    post:
      tags: [negotiation-messages]
      summary: Create negotiation message
      operationId: createNegotiationMessage
      parameters:
        - $ref: '#/components/parameters/NegotiationIdParam'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/NegotiationMessageCreateRequest'
      responses:
        '201':
          description: Negotiation message created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/NegotiationMessageResponse'

  /reservations:
    get:
      tags: [reservations]
      summary: List reservations
      operationId: listReservations
      parameters:
        - $ref: '#/components/parameters/PageParam'
        - $ref: '#/components/parameters/PageSizeParam'
        - name: listingId
          in: query
          schema:
            type: string
            format: uuid
        - name: negotiationId
          in: query
          schema:
            type: string
            format: uuid
        - name: status
          in: query
          schema:
            $ref: '#/components/schemas/ReservationStatus'
      responses:
        '200':
          description: Reservations list
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedReservationsResponse'
    post:
      tags: [reservations]
      summary: Create reservation
      operationId: createReservation
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ReservationCreateRequest'
      responses:
        '201':
          description: Reservation created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ReservationResponse'

  /reservations/{reservationId}:
    get:
      tags: [reservations]
      summary: Get reservation detail
      operationId: getReservation
      parameters:
        - $ref: '#/components/parameters/ReservationIdParam'
      responses:
        '200':
          description: Reservation detail
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ReservationResponse'

  /reservations/{reservationId}/status:
    patch:
      tags: [reservations]
      summary: Transition reservation status
      operationId: transitionReservationStatus
      parameters:
        - $ref: '#/components/parameters/ReservationIdParam'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ReservationStatusTransitionRequest'
      responses:
        '200':
          description: Reservation status updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ReservationResponse'
        '400':
          $ref: '#/components/responses/InvalidTransitionError'

  /reservations/{reservationId}/available-transitions:
    get:
      tags: [reservations]
      summary: Get reservation transitions allowed for current user
      operationId: getReservationAvailableTransitions
      parameters:
        - $ref: '#/components/parameters/ReservationIdParam'
      responses:
        '200':
          description: Allowed transitions
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AvailableTransitionsResponse'

  /logistics-jobs:
    get:
      tags: [logistics]
      summary: List logistics jobs
      operationId: listLogisticsJobs
      parameters:
        - $ref: '#/components/parameters/PageParam'
        - $ref: '#/components/parameters/PageSizeParam'
        - name: listingId
          in: query
          schema:
            type: string
            format: uuid
        - name: negotiationId
          in: query
          schema:
            type: string
            format: uuid
        - name: reservationId
          in: query
          schema:
            type: string
            format: uuid
        - name: logisticsCompanyId
          in: query
          schema:
            type: string
            format: uuid
        - name: status
          in: query
          schema:
            $ref: '#/components/schemas/LogisticsJobStatus'
      responses:
        '200':
          description: Logistics jobs list
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedLogisticsJobsResponse'
    post:
      tags: [logistics]
      summary: Create logistics job
      operationId: createLogisticsJob
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/LogisticsJobCreateRequest'
      responses:
        '201':
          description: Logistics job created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/LogisticsJobResponse'

  /logistics-jobs/{jobId}:
    get:
      tags: [logistics]
      summary: Get logistics job detail
      operationId: getLogisticsJob
      parameters:
        - $ref: '#/components/parameters/JobIdParam'
      responses:
        '200':
          description: Logistics job detail
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/LogisticsJobResponse'
    patch:
      tags: [logistics]
      summary: Update logistics job
      operationId: updateLogisticsJob
      parameters:
        - $ref: '#/components/parameters/JobIdParam'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/LogisticsJobUpdateRequest'
      responses:
        '200':
          description: Logistics job updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/LogisticsJobResponse'

  /documents:
    get:
      tags: [documents]
      summary: List documents
      operationId: listDocuments
      parameters:
        - $ref: '#/components/parameters/PageParam'
        - $ref: '#/components/parameters/PageSizeParam'
        - name: status
          in: query
          schema:
            $ref: '#/components/schemas/DocumentStatus'
        - name: documentType
          in: query
          schema:
            $ref: '#/components/schemas/DocumentType'
        - name: accessScope
          in: query
          schema:
            $ref: '#/components/schemas/DocumentAccessScope'
        - name: uploadedByUserId
          in: query
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Documents list
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedDocumentsResponse'
    post:
      tags: [documents]
      summary: Create document metadata after upload or reserve upload intent
      operationId: createDocument
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/DocumentCreateRequest'
      responses:
        '201':
          description: Document created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DocumentResponse'

  /documents/upload-intents:
    post:
      tags: [documents]
      summary: Create upload intent for document
      operationId: createDocumentUploadIntent
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/DocumentUploadIntentRequest'
      responses:
        '201':
          description: Upload intent created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DocumentUploadIntentResponse'

  /documents/{documentId}:
    get:
      tags: [documents]
      summary: Get document detail
      operationId: getDocument
      parameters:
        - $ref: '#/components/parameters/DocumentIdParam'
      responses:
        '200':
          description: Document detail
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DocumentResponse'
    patch:
      tags: [documents]
      summary: Update document metadata
      operationId: updateDocument
      parameters:
        - $ref: '#/components/parameters/DocumentIdParam'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/DocumentUpdateRequest'
      responses:
        '200':
          description: Document updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DocumentResponse'

  /documents/{documentId}/status:
    patch:
      tags: [documents]
      summary: Transition document status
      operationId: transitionDocumentStatus
      parameters:
        - $ref: '#/components/parameters/DocumentIdParam'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/DocumentStatusTransitionRequest'
      responses:
        '200':
          description: Document status updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DocumentResponse'
        '400':
          $ref: '#/components/responses/InvalidTransitionError'

  /documents/{documentId}/download:
    get:
      tags: [documents]
      summary: Resolve authorized document download
      operationId: resolveDocumentDownload
      parameters:
        - $ref: '#/components/parameters/DocumentIdParam'
      responses:
        '200':
          description: Download resolved
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DocumentDownloadResponse'

  /document-links:
    get:
      tags: [document-links]
      summary: List document links
      operationId: listDocumentLinks
      parameters:
        - name: documentId
          in: query
          schema:
            type: string
            format: uuid
        - name: relatedEntityType
          in: query
          schema:
            $ref: '#/components/schemas/RelatedEntityType'
        - name: relatedEntityId
          in: query
          schema:
            type: string
            format: uuid
        - name: relationType
          in: query
          schema:
            $ref: '#/components/schemas/DocumentRelationType'
        - name: status
          in: query
          schema:
            $ref: '#/components/schemas/DocumentLinkStatus'
      responses:
        '200':
          description: Document links list
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedDocumentLinksResponse'
    post:
      tags: [document-links]
      summary: Link document to business entity
      operationId: createDocumentLink
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/DocumentLinkCreateRequest'
      responses:
        '201':
          description: Document link created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DocumentLinkResponse'

  /document-links/{documentLinkId}:
    patch:
      tags: [document-links]
      summary: Update document link
      operationId: updateDocumentLink
      parameters:
        - $ref: '#/components/parameters/DocumentLinkIdParam'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/DocumentLinkUpdateRequest'
      responses:
        '200':
          description: Document link updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DocumentLinkResponse'

  /compliance-cases:
    get:
      tags: [compliance-cases]
      summary: List compliance cases
      operationId: listComplianceCases
      parameters:
        - $ref: '#/components/parameters/PageParam'
        - $ref: '#/components/parameters/PageSizeParam'
        - name: caseType
          in: query
          schema:
            $ref: '#/components/schemas/ComplianceCaseType'
        - name: relatedEntityType
          in: query
          schema:
            $ref: '#/components/schemas/RelatedEntityType'
        - name: relatedEntityId
          in: query
          schema:
            type: string
            format: uuid
        - name: assignedToUserId
          in: query
          schema:
            type: string
            format: uuid
        - name: status
          in: query
          schema:
            $ref: '#/components/schemas/ComplianceCaseStatus'
      responses:
        '200':
          description: Compliance cases list
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedComplianceCasesResponse'
    post:
      tags: [compliance-cases]
      summary: Create compliance case
      operationId: createComplianceCase
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ComplianceCaseCreateRequest'
      responses:
        '201':
          description: Compliance case created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ComplianceCaseResponse'

  /compliance-cases/{caseId}:
    get:
      tags: [compliance-cases]
      summary: Get compliance case detail
      operationId: getComplianceCase
      parameters:
        - $ref: '#/components/parameters/CaseIdParam'
      responses:
        '200':
          description: Compliance case detail
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ComplianceCaseResponse'
    patch:
      tags: [compliance-cases]
      summary: Update compliance case
      operationId: updateComplianceCase
      parameters:
        - $ref: '#/components/parameters/CaseIdParam'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ComplianceCaseUpdateRequest'
      responses:
        '200':
          description: Compliance case updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ComplianceCaseResponse'

  /notifications:
    get:
      tags: [notifications]
      summary: List notifications for current user or filtered scope
      operationId: listNotifications
      parameters:
        - $ref: '#/components/parameters/PageParam'
        - $ref: '#/components/parameters/PageSizeParam'
        - name: status
          in: query
          schema:
            $ref: '#/components/schemas/NotificationStatus'
        - name: channel
          in: query
          schema:
            $ref: '#/components/schemas/NotificationChannel'
        - name: notificationType
          in: query
          schema:
            $ref: '#/components/schemas/NotificationType'
      responses:
        '200':
          description: Notifications list
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedNotificationsResponse'

  /notifications/{notificationId}/read:
    post:
      tags: [notifications]
      summary: Mark notification as read
      operationId: markNotificationRead
      parameters:
        - $ref: '#/components/parameters/NotificationIdParam'
      responses:
        '200':
          description: Notification marked read
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/NotificationResponse'

  /analytics/events:
    post:
      tags: [analytics]
      summary: Record analytics event
      operationId: createAnalyticsEvent
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/AnalyticsEventCreateRequest'
      responses:
        '201':
          description: Analytics event recorded
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AnalyticsEventResponse'

  /audit-events:
    get:
      tags: [audit]
      summary: List audit events
      operationId: listAuditEvents
      parameters:
        - $ref: '#/components/parameters/PageParam'
        - $ref: '#/components/parameters/PageSizeParam'
        - name: actorUserId
          in: query
          schema:
            type: string
            format: uuid
        - name: entityType
          in: query
          schema:
            $ref: '#/components/schemas/RelatedEntityType'
        - name: entityId
          in: query
          schema:
            type: string
            format: uuid
        - name: actionCode
          in: query
          schema:
            type: string
        - name: occurredFrom
          in: query
          schema:
            type: string
            format: date-time
        - name: occurredTo
          in: query
          schema:
            type: string
            format: date-time
        - name: correlationId
          in: query
          schema:
            type: string
      responses:
        '200':
          description: Audit events list
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedAuditEventsResponse'

  /admin/dashboard:
    get:
      tags: [admin]
      summary: Get admin dashboard summary
      operationId: getAdminDashboard
      responses:
        '200':
          description: Admin dashboard summary
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AdminDashboardResponse'

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  parameters:
    PageParam:
      name: page
      in: query
      schema:
        type: integer
        minimum: 1
        default: 1
    PageSizeParam:
      name: pageSize
      in: query
      schema:
        type: integer
        minimum: 1
        maximum: 100
        default: 25
    UserIdParam:
      name: userId
      in: path
      required: true
      schema:
        type: string
        format: uuid
    CompanyIdParam:
      name: companyId
      in: path
      required: true
      schema:
        type: string
        format: uuid
    AssignmentIdParam:
      name: assignmentId
      in: path
      required: true
      schema:
        type: string
        format: uuid
    MembershipIdParam:
      name: membershipId
      in: path
      required: true
      schema:
        type: string
        format: uuid
    ReviewIdParam:
      name: reviewId
      in: path
      required: true
      schema:
        type: string
        format: uuid
    CategoryIdParam:
      name: categoryId
      in: path
      required: true
      schema:
        type: string
        format: uuid
    SubtypeIdParam:
      name: subtypeId
      in: path
      required: true
      schema:
        type: string
        format: uuid
    ListingIdParam:
      name: listingId
      in: path
      required: true
      schema:
        type: string
        format: uuid
    ListingPhotoIdParam:
      name: listingPhotoId
      in: path
      required: true
      schema:
        type: string
        format: uuid
    InquiryIdParam:
      name: inquiryId
      in: path
      required: true
      schema:
        type: string
        format: uuid
    NegotiationIdParam:
      name: negotiationId
      in: path
      required: true
      schema:
        type: string
        format: uuid
    ReservationIdParam:
      name: reservationId
      in: path
      required: true
      schema:
        type: string
        format: uuid
    JobIdParam:
      name: jobId
      in: path
      required: true
      schema:
        type: string
        format: uuid
    DocumentIdParam:
      name: documentId
      in: path
      required: true
      schema:
        type: string
        format: uuid
    DocumentLinkIdParam:
      name: documentLinkId
      in: path
      required: true
      schema:
        type: string
        format: uuid
    CaseIdParam:
      name: caseId
      in: path
      required: true
      schema:
        type: string
        format: uuid
    NotificationIdParam:
      name: notificationId
      in: path
      required: true
      schema:
        type: string
        format: uuid

  responses:
    UnauthorizedError:
      description: Authentication required or invalid token
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
    ForbiddenError:
      description: Access denied
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
    NotFoundError:
      description: Resource not found
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
    ConflictError:
      description: Resource conflict
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
    ValidationError:
      description: Request validation failed
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ValidationErrorResponse'
    InvalidTransitionError:
      description: Invalid workflow transition
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/InvalidTransitionErrorResponse'

  schemas:
    HealthResponse:
      type: object
      required: [status, version, timestamp]
      properties:
        status:
          type: string
          example: ok
        version:
          type: string
        timestamp:
          type: string
          format: date-time

    ErrorResponse:
      type: object
      required: [code, message]
      properties:
        code:
          type: string
        message:
          type: string
        correlationId:
          type: string
          nullable: true
        details:
          type: object
          additionalProperties: true
          nullable: true

    ValidationErrorResponse:
      allOf:
        - $ref: '#/components/schemas/ErrorResponse'
        - type: object
          properties:
            fieldErrors:
              type: array
              items:
                $ref: '#/components/schemas/FieldError'

    InvalidTransitionErrorResponse:
      allOf:
        - $ref: '#/components/schemas/ErrorResponse'
        - type: object
          required: [currentStatus, attemptedStatus]
          properties:
            currentStatus:
              type: string
            attemptedStatus:
              type: string
            allowedTransitions:
              type: array
              items:
                type: string

    FieldError:
      type: object
      required: [field, message]
      properties:
        field:
          type: string
        message:
          type: string

    PaginationMeta:
      type: object
      required: [page, pageSize, total]
      properties:
        page:
          type: integer
        pageSize:
          type: integer
        total:
          type: integer

    AvailableTransition:
      type: object
      required: [toStatus]
      properties:
        toStatus:
          type: string
        label:
          type: string
          nullable: true
        reasonRequired:
          type: boolean
          default: false

    AvailableTransitionsResponse:
      type: object
      required: [resourceId, resourceType, currentStatus, transitions]
      properties:
        resourceId:
          type: string
          format: uuid
        resourceType:
          type: string
        currentStatus:
          type: string
        transitions:
          type: array
          items:
            $ref: '#/components/schemas/AvailableTransition'

    BaseAuditFields:
      type: object
      required: [id, status, createdAt, updatedAt]
      properties:
        id:
          type: string
          format: uuid
        status:
          type: string
        createdAt:
          type: string
          format: date-time
        createdByUserId:
          type: string
          format: uuid
          nullable: true
        updatedAt:
          type: string
          format: date-time
        updatedByUserId:
          type: string
          format: uuid
          nullable: true

    LoginRequest:
      type: object
      required: [email, password]
      properties:
        email:
          type: string
          format: email
        password:
          type: string
          format: password

    RefreshTokenRequest:
      type: object
      required: [refreshToken]
      properties:
        refreshToken:
          type: string

    LogoutRequest:
      type: object
      properties:
        refreshToken:
          type: string
          nullable: true

    AuthTokenPairResponse:
      type: object
      required: [accessToken, refreshToken, tokenType, expiresIn]
      properties:
        accessToken:
          type: string
        refreshToken:
          type: string
        tokenType:
          type: string
          example: Bearer
        expiresIn:
          type: integer

    CurrentUserResponse:
      type: object
      required: [user, roleCodes, memberships]
      properties:
        user:
          $ref: '#/components/schemas/User'
        roleCodes:
          type: array
          items:
            $ref: '#/components/schemas/RoleCode'
        memberships:
          type: array
          items:
            $ref: '#/components/schemas/CompanyMembership'

    UserStatus:
      type: string
      enum: [invited, active, suspended, deactivated]

    RoleStatus:
      type: string
      enum: [active, inactive]

    RoleCode:
      type: string
      enum: [platform_admin, compliance_operator, seller_company_user, buyer_company_user, logistics_partner, auditor_viewer]

    UserRoleAssignmentStatus:
      type: string
      enum: [active, revoked]

    CompanyStatus:
      type: string
      enum: [draft, verification_submitted, verified, rejected, suspended, inactive]

    CompanyType:
      type: string
      enum: [seller, buyer, seller_buyer, logistics_partner]

    CompanyMembershipStatus:
      type: string
      enum: [invited, active, inactive, removed]

    CompanyMembershipRole:
      type: string
      enum: [owner, admin, member, compliance_contact, sales_contact, logistics_contact, viewer]

    CompanyVerificationReviewStatus:
      type: string
      enum: [submitted, in_review, approved, rejected, correction_requested]

    TaxonomyStatus:
      type: string
      enum: [active, inactive]

    ListingStatus:
      type: string
      enum: [draft, submitted, compliance_review, approved, published, inquiry_open, negotiation, reserved, completed, archived, rejected, expired, disputed, cancelled]

    UnitCode:
      type: string
      enum: [kg, tonne, litre, m3, piece, pallet, batch]

    PriceModel:
      type: string
      enum: [fixed_price, price_on_request, negotiable, indexed]

    ListingPhotoStatus:
      type: string
      enum: [active, removed]

    ListingComplianceReviewStatus:
      type: string
      enum: [submitted, in_review, approved, rejected, correction_requested]

    InquiryStatus:
      type: string
      enum: [open, responded, closed, cancelled]

    NegotiationStatus:
      type: string
      enum: [open, reserved, completed, disputed, cancelled, closed]

    NegotiationMessageStatus:
      type: string
      enum: [active, withdrawn]

    NegotiationMessageType:
      type: string
      enum: [message, offer, counter_offer, clarification, system_note]

    ReservationStatus:
      type: string
      enum: [active, released, completed, expired, cancelled]

    LogisticsJobStatus:
      type: string
      enum: [planned, in_progress, completed, cancelled]

    DocumentStatus:
      type: string
      enum: [uploaded, active, replaced, archived, deleted]

    DocumentType:
      type: string
      enum: [company_verification_file, listing_photo, certification, test_report, contract_supporting_file, shipment_related_file, inquiry_attachment, negotiation_attachment, compliance_evidence]

    DocumentAccessScope:
      type: string
      enum: [private, company_restricted, counterparty_shared, compliance_only, admin_only]

    DocumentLinkStatus:
      type: string
      enum: [active, removed]

    RelatedEntityType:
      type: string
      enum: [company, listing, inquiry, negotiation, reservation, document]

    DocumentRelationType:
      type: string
      enum: [verification_evidence, listing_photo, quality_certificate, test_report, inquiry_attachment, negotiation_attachment, shipment_record, completion_evidence]

    ComplianceCaseStatus:
      type: string
      enum: [open, in_review, resolved, rejected, cancelled]

    ComplianceCaseType:
      type: string
      enum: [company_verification, listing_review, dispute, document_issue]

    NotificationStatus:
      type: string
      enum: [pending, sent, read, failed]

    NotificationChannel:
      type: string
      enum: [in_app, email]

    NotificationType:
      type: string
      enum: [company_verification_submitted, company_verification_approved, company_verification_rejected, listing_submitted, listing_approved, listing_rejected, listing_published, inquiry_created, inquiry_responded, negotiation_opened, reservation_created, reservation_expired, dispute_opened, document_shared]

    AuditEventStatus:
      type: string
      enum: [recorded]

    AuditActorType:
      type: string
      enum: [user, system]

    AnalyticsEventStatus:
      type: string
      enum: [recorded]

    User:
      allOf:
        - $ref: '#/components/schemas/BaseAuditFields'
        - type: object
          required: [email, firstName, lastName]
          properties:
            status:
              $ref: '#/components/schemas/UserStatus'
            email:
              type: string
              format: email
            firstName:
              type: string
            lastName:
              type: string
            displayName:
              type: string
              nullable: true
            phone:
              type: string
              nullable: true
            locale:
              type: string
              nullable: true
            timezone:
              type: string
              nullable: true
            lastLoginAt:
              type: string
              format: date-time
              nullable: true

    Role:
      allOf:
        - $ref: '#/components/schemas/BaseAuditFields'
        - type: object
          required: [code, name]
          properties:
            status:
              $ref: '#/components/schemas/RoleStatus'
            code:
              $ref: '#/components/schemas/RoleCode'
            name:
              type: string
            description:
              type: string
              nullable: true

    UserRoleAssignment:
      allOf:
        - $ref: '#/components/schemas/BaseAuditFields'
        - type: object
          required: [userId, roleId, assignedAt]
          properties:
            status:
              $ref: '#/components/schemas/UserRoleAssignmentStatus'
            userId:
              type: string
              format: uuid
            roleId:
              type: string
              format: uuid
            assignedAt:
              type: string
              format: date-time
            assignedByUserId:
              type: string
              format: uuid
            revokedAt:
              type: string
              format: date-time
              nullable: true
            revokedByUserId:
              type: string
              format: uuid
              nullable: true

    Company:
      allOf:
        - $ref: '#/components/schemas/BaseAuditFields'
        - type: object
          required: [legalName, registrationNumber, companyType, countryCode, addressLine1, city, postalCode, sellerCapability, buyerCapability, logisticsCapability]
          properties:
            status:
              $ref: '#/components/schemas/CompanyStatus'
            legalName:
              type: string
            tradingName:
              type: string
              nullable: true
            registrationNumber:
              type: string
            taxIdentifier:
              type: string
              nullable: true
            companyType:
              $ref: '#/components/schemas/CompanyType'
            email:
              type: string
              format: email
              nullable: true
            phone:
              type: string
              nullable: true
            websiteUrl:
              type: string
              format: uri
              nullable: true
            countryCode:
              type: string
              minLength: 2
              maxLength: 2
            addressLine1:
              type: string
            addressLine2:
              type: string
              nullable: true
            city:
              type: string
            postalCode:
              type: string
            latitude:
              type: number
              nullable: true
            longitude:
              type: number
              nullable: true
            sellerCapability:
              type: boolean
            buyerCapability:
              type: boolean
            logisticsCapability:
              type: boolean
            verificationSubmittedAt:
              type: string
              format: date-time
              nullable: true
            verificationReviewedAt:
              type: string
              format: date-time
              nullable: true
            verificationReviewedByUserId:
              type: string
              format: uuid
              nullable: true
            verifiedAt:
              type: string
              format: date-time
              nullable: true
            verifiedByUserId:
              type: string
              format: uuid
              nullable: true
            rejectedAt:
              type: string
              format: date-time
              nullable: true
            rejectedByUserId:
              type: string
              format: uuid
              nullable: true

    CompanyMembership:
      allOf:
        - $ref: '#/components/schemas/BaseAuditFields'
        - type: object
          required: [companyId, userId, membershipRole, isPrimaryContact]
          properties:
            status:
              $ref: '#/components/schemas/CompanyMembershipStatus'
            companyId:
              type: string
              format: uuid
            userId:
              type: string
              format: uuid
            membershipRole:
              $ref: '#/components/schemas/CompanyMembershipRole'
            isPrimaryContact:
              type: boolean
            invitedAt:
              type: string
              format: date-time
              nullable: true
            joinedAt:
              type: string
              format: date-time
              nullable: true
            leftAt:
              type: string
              format: date-time
              nullable: true

    CompanyVerificationReview:
      allOf:
        - $ref: '#/components/schemas/BaseAuditFields'
        - type: object
          required: [companyId, submittedByUserId, submittedAt]
          properties:
            status:
              $ref: '#/components/schemas/CompanyVerificationReviewStatus'
            companyId:
              type: string
              format: uuid
            submittedByUserId:
              type: string
              format: uuid
            reviewerUserId:
              type: string
              format: uuid
              nullable: true
            submissionNotes:
              type: string
              nullable: true
            reviewerNotes:
              type: string
              nullable: true
            rejectionReasonCode:
              type: string
              nullable: true
            submittedAt:
              type: string
              format: date-time
            reviewedAt:
              type: string
              format: date-time
              nullable: true
            approvedAt:
              type: string
              format: date-time
              nullable: true
            rejectedAt:
              type: string
              format: date-time
              nullable: true

    MaterialCategory:
      allOf:
        - $ref: '#/components/schemas/BaseAuditFields'
        - type: object
          required: [code, name, sortOrder]
          properties:
            status:
              $ref: '#/components/schemas/TaxonomyStatus'
            code:
              type: string
            name:
              type: string
            description:
              type: string
              nullable: true
            sortOrder:
              type: integer

    MaterialSubtype:
      allOf:
        - $ref: '#/components/schemas/BaseAuditFields'
        - type: object
          required: [categoryId, code, name, sortOrder]
          properties:
            status:
              $ref: '#/components/schemas/TaxonomyStatus'
            categoryId:
              type: string
              format: uuid
            code:
              type: string
            name:
              type: string
            description:
              type: string
              nullable: true
            sortOrder:
              type: integer

    Listing:
      allOf:
        - $ref: '#/components/schemas/BaseAuditFields'
        - type: object
          required: [sellerCompanyId, materialCategoryId, materialSubtypeId, title, quantity, unit, contaminationNotes, originLocationText, availabilityStartDate, availabilityEndDate, priceModel]
          properties:
            status:
              $ref: '#/components/schemas/ListingStatus'
            sellerCompanyId:
              type: string
              format: uuid
            materialCategoryId:
              type: string
              format: uuid
            materialSubtypeId:
              type: string
              format: uuid
            title:
              type: string
            description:
              type: string
              nullable: true
            quantity:
              type: number
            unit:
              $ref: '#/components/schemas/UnitCode'
            purityDescription:
              type: string
              nullable: true
            qualityIndicators:
              type: object
              additionalProperties: true
              nullable: true
            contaminationNotes:
              type: string
            originLocationText:
              type: string
            originLatitude:
              type: number
              nullable: true
            originLongitude:
              type: number
              nullable: true
            pickupTerms:
              type: string
              nullable: true
            deliveryTerms:
              type: string
              nullable: true
            availabilityStartDate:
              type: string
              format: date
            availabilityEndDate:
              type: string
              format: date
            priceModel:
              $ref: '#/components/schemas/PriceModel'
            priceAmount:
              type: number
              nullable: true
            priceCurrencyCode:
              type: string
              nullable: true
            sellerReferenceCode:
              type: string
              nullable: true
            submittedAt:
              type: string
              format: date-time
              nullable: true
            submittedByUserId:
              type: string
              format: uuid
              nullable: true
            reviewedAt:
              type: string
              format: date-time
              nullable: true
            reviewedByUserId:
              type: string
              format: uuid
              nullable: true
            approvedAt:
              type: string
              format: date-time
              nullable: true
            approvedByUserId:
              type: string
              format: uuid
              nullable: true
            rejectedAt:
              type: string
              format: date-time
              nullable: true
            rejectedByUserId:
              type: string
              format: uuid
              nullable: true
            rejectionReasonCode:
              type: string
              nullable: true
            inquiryOpenedAt:
              type: string
              format: date-time
              nullable: true
            reservedAt:
              type: string
              format: date-time
              nullable: true
            completedAt:
              type: string
              format: date-time
              nullable: true
            archivedAt:
              type: string
              format: date-time
              nullable: true
            expiresAt:
              type: string
              format: date-time
              nullable: true

    ListingPhoto:
      allOf:
        - $ref: '#/components/schemas/BaseAuditFields'
        - type: object
          required: [listingId, documentId, sortOrder, isPrimary]
          properties:
            status:
              $ref: '#/components/schemas/ListingPhotoStatus'
            listingId:
              type: string
              format: uuid
            documentId:
              type: string
              format: uuid
            sortOrder:
              type: integer
            isPrimary:
              type: boolean
            caption:
              type: string
              nullable: true

    ListingComplianceReview:
      allOf:
        - $ref: '#/components/schemas/BaseAuditFields'
        - type: object
          required: [listingId, submittedAt]
          properties:
            status:
              $ref: '#/components/schemas/ListingComplianceReviewStatus'
            listingId:
              type: string
              format: uuid
            reviewerUserId:
              type: string
              format: uuid
              nullable: true
            submissionNotes:
              type: string
              nullable: true
            reviewerNotes:
              type: string
              nullable: true
            rejectionReasonCode:
              type: string
              nullable: true
            submittedAt:
              type: string
              format: date-time
            reviewStartedAt:
              type: string
              format: date-time
              nullable: true
            reviewedAt:
              type: string
              format: date-time
              nullable: true
            approvedAt:
              type: string
              format: date-time
              nullable: true
            rejectedAt:
              type: string
              format: date-time
              nullable: true

    Inquiry:
      allOf:
        - $ref: '#/components/schemas/BaseAuditFields'
        - type: object
          required: [listingId, buyerCompanyId, buyerContactUserId, requestedQuantity, requestedUnit, buyerMessage, openedAt]
          properties:
            status:
              $ref: '#/components/schemas/InquiryStatus'
            listingId:
              type: string
              format: uuid
            buyerCompanyId:
              type: string
              format: uuid
            buyerContactUserId:
              type: string
              format: uuid
            requestedQuantity:
              type: number
            requestedUnit:
              $ref: '#/components/schemas/UnitCode'
            buyerMessage:
              type: string
            intendedUseNotes:
              type: string
              nullable: true
            responseDueAt:
              type: string
              format: date-time
              nullable: true
            openedAt:
              type: string
              format: date-time
            respondedAt:
              type: string
              format: date-time
              nullable: true
            closedAt:
              type: string
              format: date-time
              nullable: true

    Negotiation:
      allOf:
        - $ref: '#/components/schemas/BaseAuditFields'
        - type: object
          required: [inquiryId, listingId, sellerCompanyId, buyerCompanyId, openedAt]
          properties:
            status:
              $ref: '#/components/schemas/NegotiationStatus'
            inquiryId:
              type: string
              format: uuid
            listingId:
              type: string
              format: uuid
            sellerCompanyId:
              type: string
              format: uuid
            buyerCompanyId:
              type: string
              format: uuid
            openedAt:
              type: string
              format: date-time
            closedAt:
              type: string
              format: date-time
              nullable: true
            closeReasonCode:
              type: string
              nullable: true

    NegotiationMessage:
      allOf:
        - $ref: '#/components/schemas/BaseAuditFields'
        - type: object
          required: [negotiationId, authorUserId, messageType, body]
          properties:
            status:
              $ref: '#/components/schemas/NegotiationMessageStatus'
            negotiationId:
              type: string
              format: uuid
            authorUserId:
              type: string
              format: uuid
            messageType:
              $ref: '#/components/schemas/NegotiationMessageType'
            body:
              type: string
            proposedQuantity:
              type: number
              nullable: true
            proposedUnit:
              $ref: '#/components/schemas/UnitCode'
              nullable: true
            proposedPriceModel:
              $ref: '#/components/schemas/PriceModel'
              nullable: true
            proposedPriceAmount:
              type: number
              nullable: true
            proposedCurrencyCode:
              type: string
              nullable: true
            proposedPickupTerms:
              type: string
              nullable: true
            proposedDeliveryTerms:
              type: string
              nullable: true

    Reservation:
      allOf:
        - $ref: '#/components/schemas/BaseAuditFields'
        - type: object
          required: [listingId, negotiationId, reservedQuantity, reservedUnit, reservedAt]
          properties:
            status:
              $ref: '#/components/schemas/ReservationStatus'
            listingId:
              type: string
              format: uuid
            negotiationId:
              type: string
              format: uuid
            reservedQuantity:
              type: number
            reservedUnit:
              $ref: '#/components/schemas/UnitCode'
            reservedAt:
              type: string
              format: date-time
            expiresAt:
              type: string
              format: date-time
              nullable: true
            releasedAt:
              type: string
              format: date-time
              nullable: true
            completedAt:
              type: string
              format: date-time
              nullable: true

    LogisticsJob:
      allOf:
        - $ref: '#/components/schemas/BaseAuditFields'
        - type: object
          required: [listingId, logisticsCompanyId, pickupLocationText]
          properties:
            status:
              $ref: '#/components/schemas/LogisticsJobStatus'
            listingId:
              type: string
              format: uuid
            negotiationId:
              type: string
              format: uuid
              nullable: true
            reservationId:
              type: string
              format: uuid
              nullable: true
            logisticsCompanyId:
              type: string
              format: uuid
            pickupLocationText:
              type: string
            deliveryLocationText:
              type: string
              nullable: true
            scheduledPickupAt:
              type: string
              format: date-time
              nullable: true
            scheduledDeliveryAt:
              type: string
              format: date-time
              nullable: true
            executionNotes:
              type: string
              nullable: true

    Document:
      allOf:
        - $ref: '#/components/schemas/BaseAuditFields'
        - type: object
          required: [documentType, storageKey, originalFileName, contentType, fileSizeBytes, uploadedByUserId, uploadedAt, accessScope]
          properties:
            status:
              $ref: '#/components/schemas/DocumentStatus'
            documentType:
              $ref: '#/components/schemas/DocumentType'
            storageKey:
              type: string
            originalFileName:
              type: string
            contentType:
              type: string
            fileSizeBytes:
              type: integer
              format: int64
            checksum:
              type: string
              nullable: true
            title:
              type: string
              nullable: true
            description:
              type: string
              nullable: true
            uploadedByUserId:
              type: string
              format: uuid
            uploadedAt:
              type: string
              format: date-time
            accessScope:
              $ref: '#/components/schemas/DocumentAccessScope'

    DocumentLink:
      allOf:
        - $ref: '#/components/schemas/BaseAuditFields'
        - type: object
          required: [documentId, relatedEntityType, relatedEntityId, relationType, visibleToCounterparty]
          properties:
            status:
              $ref: '#/components/schemas/DocumentLinkStatus'
            documentId:
              type: string
              format: uuid
            relatedEntityType:
              $ref: '#/components/schemas/RelatedEntityType'
            relatedEntityId:
              type: string
              format: uuid
            relationType:
              $ref: '#/components/schemas/DocumentRelationType'
            visibleToCounterparty:
              type: boolean

    ComplianceCase:
      allOf:
        - $ref: '#/components/schemas/BaseAuditFields'
        - type: object
          required: [caseType, relatedEntityType, relatedEntityId, openedAt]
          properties:
            status:
              $ref: '#/components/schemas/ComplianceCaseStatus'
            caseType:
              $ref: '#/components/schemas/ComplianceCaseType'
            relatedEntityType:
              $ref: '#/components/schemas/RelatedEntityType'
            relatedEntityId:
              type: string
              format: uuid
            assignedToUserId:
              type: string
              format: uuid
              nullable: true
            openedAt:
              type: string
              format: date-time
            resolvedAt:
              type: string
              format: date-time
              nullable: true
            resolutionCode:
              type: string
              nullable: true
            internalNotes:
              type: string
              nullable: true

    Notification:
      allOf:
        - $ref: '#/components/schemas/BaseAuditFields'
        - type: object
          required: [userId, notificationType, channel, title, body]
          properties:
            status:
              $ref: '#/components/schemas/NotificationStatus'
            userId:
              type: string
              format: uuid
            notificationType:
              $ref: '#/components/schemas/NotificationType'
            channel:
              $ref: '#/components/schemas/NotificationChannel'
            title:
              type: string
            body:
              type: string
            relatedEntityType:
              $ref: '#/components/schemas/RelatedEntityType'
              nullable: true
            relatedEntityId:
              type: string
              format: uuid
              nullable: true
            sentAt:
              type: string
              format: date-time
              nullable: true
            readAt:
              type: string
              format: date-time
              nullable: true

    AnalyticsEvent:
      allOf:
        - $ref: '#/components/schemas/BaseAuditFields'
        - type: object
          required: [eventName, eventTimestamp]
          properties:
            status:
              $ref: '#/components/schemas/AnalyticsEventStatus'
            eventName:
              type: string
            userId:
              type: string
              format: uuid
              nullable: true
            companyId:
              type: string
              format: uuid
              nullable: true
            relatedEntityType:
              $ref: '#/components/schemas/RelatedEntityType'
              nullable: true
            relatedEntityId:
              type: string
              format: uuid
              nullable: true
            eventTimestamp:
              type: string
              format: date-time
            eventPayload:
              type: object
              additionalProperties: true
              nullable: true

    AuditEvent:
      type: object
      required: [id, status, actorType, entityType, entityId, actionCode, occurredAt, createdAt, updatedAt]
      properties:
        id:
          type: string
          format: uuid
        status:
          $ref: '#/components/schemas/AuditEventStatus'
        actorUserId:
          type: string
          format: uuid
          nullable: true
        actorType:
          $ref: '#/components/schemas/AuditActorType'
        entityType:
          $ref: '#/components/schemas/RelatedEntityType'
        entityId:
          type: string
          format: uuid
        actionCode:
          type: string
        beforeSnapshot:
          type: object
          additionalProperties: true
          nullable: true
        afterSnapshot:
          type: object
          additionalProperties: true
          nullable: true
        reasonCode:
          type: string
          nullable: true
        occurredAt:
          type: string
          format: date-time
        correlationId:
          type: string
          nullable: true
        createdAt:
          type: string
          format: date-time
        createdByUserId:
          type: string
          format: uuid
          nullable: true
        updatedAt:
          type: string
          format: date-time
        updatedByUserId:
          type: string
          format: uuid
          nullable: true

    UserCreateRequest:
      type: object
      required: [email, password, firstName, lastName]
      properties:
        email:
          type: string
          format: email
        password:
          type: string
          minLength: 8
        firstName:
          type: string
        lastName:
          type: string
        displayName:
          type: string
          nullable: true
        phone:
          type: string
          nullable: true
        locale:
          type: string
          nullable: true
        timezone:
          type: string
          nullable: true

    UserUpdateRequest:
      type: object
      properties:
        firstName:
          type: string
        lastName:
          type: string
        displayName:
          type: string
          nullable: true
        phone:
          type: string
          nullable: true
        locale:
          type: string
          nullable: true
        timezone:
          type: string
          nullable: true

    UserStatusTransitionRequest:
      type: object
      required: [toStatus]
      properties:
        toStatus:
          $ref: '#/components/schemas/UserStatus'
        reasonCode:
          type: string
          nullable: true

    UserRoleAssignmentCreateRequest:
      type: object
      required: [userId, roleId]
      properties:
        userId:
          type: string
          format: uuid
        roleId:
          type: string
          format: uuid

    RevocationRequest:
      type: object
      properties:
        reasonCode:
          type: string
          nullable: true

    CompanyCreateRequest:
      type: object
      required: [legalName, registrationNumber, companyType, countryCode, addressLine1, city, postalCode, sellerCapability, buyerCapability, logisticsCapability]
      properties:
        legalName:
          type: string
        tradingName:
          type: string
          nullable: true
        registrationNumber:
          type: string
        taxIdentifier:
          type: string
          nullable: true
        companyType:
          $ref: '#/components/schemas/CompanyType'
        email:
          type: string
          format: email
          nullable: true
        phone:
          type: string
          nullable: true
        websiteUrl:
          type: string
          format: uri
          nullable: true
        countryCode:
          type: string
          minLength: 2
          maxLength: 2
        addressLine1:
          type: string
        addressLine2:
          type: string
          nullable: true
        city:
          type: string
        postalCode:
          type: string
        latitude:
          type: number
          nullable: true
        longitude:
          type: number
          nullable: true
        sellerCapability:
          type: boolean
        buyerCapability:
          type: boolean
        logisticsCapability:
          type: boolean

    CompanyUpdateRequest:
      type: object
      properties:
        legalName:
          type: string
        tradingName:
          type: string
          nullable: true
        taxIdentifier:
          type: string
          nullable: true
        email:
          type: string
          format: email
          nullable: true
        phone:
          type: string
          nullable: true
        websiteUrl:
          type: string
          format: uri
          nullable: true
        addressLine1:
          type: string
        addressLine2:
          type: string
          nullable: true
        city:
          type: string
        postalCode:
          type: string
        latitude:
          type: number
          nullable: true
        longitude:
          type: number
          nullable: true

    CompanyMembershipCreateRequest:
      type: object
      required: [userId, membershipRole]
      properties:
        userId:
          type: string
          format: uuid
        membershipRole:
          $ref: '#/components/schemas/CompanyMembershipRole'
        isPrimaryContact:
          type: boolean
          default: false

    CompanyMembershipUpdateRequest:
      type: object
      properties:
        membershipRole:
          $ref: '#/components/schemas/CompanyMembershipRole'
        isPrimaryContact:
          type: boolean

    CompanyMembershipStatusTransitionRequest:
      type: object
      required: [toStatus]
      properties:
        toStatus:
          $ref: '#/components/schemas/CompanyMembershipStatus'

    CompanyVerificationReviewCreateRequest:
      type: object
      required: [companyId]
      properties:
        companyId:
          type: string
          format: uuid
        submissionNotes:
          type: string
          nullable: true

    CompanyVerificationReviewStatusTransitionRequest:
      type: object
      required: [toStatus]
      properties:
        toStatus:
          $ref: '#/components/schemas/CompanyVerificationReviewStatus'
        reviewerNotes:
          type: string
          nullable: true
        rejectionReasonCode:
          type: string
          nullable: true

    MaterialCategoryCreateRequest:
      type: object
      required: [code, name, sortOrder]
      properties:
        code:
          type: string
        name:
          type: string
        description:
          type: string
          nullable: true
        sortOrder:
          type: integer

    MaterialCategoryUpdateRequest:
      type: object
      properties:
        name:
          type: string
        description:
          type: string
          nullable: true
        sortOrder:
          type: integer
        status:
          $ref: '#/components/schemas/TaxonomyStatus'

    MaterialSubtypeCreateRequest:
      type: object
      required: [categoryId, code, name, sortOrder]
      properties:
        categoryId:
          type: string
          format: uuid
        code:
          type: string
        name:
          type: string
        description:
          type: string
          nullable: true
        sortOrder:
          type: integer

    MaterialSubtypeUpdateRequest:
      type: object
      properties:
        categoryId:
          type: string
          format: uuid
        name:
          type: string
        description:
          type: string
          nullable: true
        sortOrder:
          type: integer
        status:
          $ref: '#/components/schemas/TaxonomyStatus'

    ListingCreateRequest:
      type: object
      required: [sellerCompanyId, materialCategoryId, materialSubtypeId, title, quantity, unit, contaminationNotes, originLocationText, availabilityStartDate, availabilityEndDate, priceModel]
      properties:
        sellerCompanyId:
          type: string
          format: uuid
        materialCategoryId:
          type: string
          format: uuid
        materialSubtypeId:
          type: string
          format: uuid
        title:
          type: string
        description:
          type: string
          nullable: true
        quantity:
          type: number
          exclusiveMinimum: 0
        unit:
          $ref: '#/components/schemas/UnitCode'
        purityDescription:
          type: string
          nullable: true
        qualityIndicators:
          type: object
          additionalProperties: true
          nullable: true
        contaminationNotes:
          type: string
        originLocationText:
          type: string
        originLatitude:
          type: number
          nullable: true
        originLongitude:
          type: number
          nullable: true
        pickupTerms:
          type: string
          nullable: true
        deliveryTerms:
          type: string
          nullable: true
        availabilityStartDate:
          type: string
          format: date
        availabilityEndDate:
          type: string
          format: date
        priceModel:
          $ref: '#/components/schemas/PriceModel'
        priceAmount:
          type: number
          nullable: true
        priceCurrencyCode:
          type: string
          nullable: true
        sellerReferenceCode:
          type: string
          nullable: true

    ListingUpdateRequest:
      type: object
      properties:
        title:
          type: string
        description:
          type: string
          nullable: true
        quantity:
          type: number
          exclusiveMinimum: 0
        unit:
          $ref: '#/components/schemas/UnitCode'
        purityDescription:
          type: string
          nullable: true
        qualityIndicators:
          type: object
          additionalProperties: true
          nullable: true
        contaminationNotes:
          type: string
        originLocationText:
          type: string
        originLatitude:
          type: number
          nullable: true
        originLongitude:
          type: number
          nullable: true
        pickupTerms:
          type: string
          nullable: true
        deliveryTerms:
          type: string
          nullable: true
        availabilityStartDate:
          type: string
          format: date
        availabilityEndDate:
          type: string
          format: date
        priceModel:
          $ref: '#/components/schemas/PriceModel'
        priceAmount:
          type: number
          nullable: true
        priceCurrencyCode:
          type: string
          nullable: true
        sellerReferenceCode:
          type: string
          nullable: true

    ListingStatusTransitionRequest:
      type: object
      required: [toStatus]
      properties:
        toStatus:
          $ref: '#/components/schemas/ListingStatus'
        reasonCode:
          type: string
          nullable: true
        note:
          type: string
          nullable: true

    ListingPhotoCreateRequest:
      type: object
      required: [documentId, sortOrder, isPrimary]
      properties:
        documentId:
          type: string
          format: uuid
        sortOrder:
          type: integer
        isPrimary:
          type: boolean
        caption:
          type: string
          nullable: true

    ListingPhotoUpdateRequest:
      type: object
      properties:
        sortOrder:
          type: integer
        isPrimary:
          type: boolean
        caption:
          type: string
          nullable: true
        status:
          $ref: '#/components/schemas/ListingPhotoStatus'

    ListingComplianceReviewCreateRequest:
      type: object
      required: [listingId]
      properties:
        listingId:
          type: string
          format: uuid
        submissionNotes:
          type: string
          nullable: true

    ListingComplianceReviewStatusTransitionRequest:
      type: object
      required: [toStatus]
      properties:
        toStatus:
          $ref: '#/components/schemas/ListingComplianceReviewStatus'
        reviewerNotes:
          type: string
          nullable: true
        rejectionReasonCode:
          type: string
          nullable: true

    InquiryCreateRequest:
      type: object
      required: [listingId, buyerCompanyId, buyerContactUserId, requestedQuantity, requestedUnit, buyerMessage]
      properties:
        listingId:
          type: string
          format: uuid
        buyerCompanyId:
          type: string
          format: uuid
        buyerContactUserId:
          type: string
          format: uuid
        requestedQuantity:
          type: number
          exclusiveMinimum: 0
        requestedUnit:
          $ref: '#/components/schemas/UnitCode'
        buyerMessage:
          type: string
        intendedUseNotes:
          type: string
          nullable: true

    InquiryUpdateRequest:
      type: object
      properties:
        requestedQuantity:
          type: number
          exclusiveMinimum: 0
        requestedUnit:
          $ref: '#/components/schemas/UnitCode'
        buyerMessage:
          type: string
        intendedUseNotes:
          type: string
          nullable: true
        responseDueAt:
          type: string
          format: date-time
          nullable: true

    InquiryStatusTransitionRequest:
      type: object
      required: [toStatus]
      properties:
        toStatus:
          $ref: '#/components/schemas/InquiryStatus'
        reasonCode:
          type: string
          nullable: true

    NegotiationCreateRequest:
      type: object
      required: [inquiryId]
      properties:
        inquiryId:
          type: string
          format: uuid

    NegotiationStatusTransitionRequest:
      type: object
      required: [toStatus]
      properties:
        toStatus:
          $ref: '#/components/schemas/NegotiationStatus'
        closeReasonCode:
          type: string
          nullable: true
        reasonCode:
          type: string
          nullable: true

    NegotiationMessageCreateRequest:
      type: object
      required: [messageType, body]
      properties:
        messageType:
          $ref: '#/components/schemas/NegotiationMessageType'
        body:
          type: string
        proposedQuantity:
          type: number
          nullable: true
        proposedUnit:
          $ref: '#/components/schemas/UnitCode'
          nullable: true
        proposedPriceModel:
          $ref: '#/components/schemas/PriceModel'
          nullable: true
        proposedPriceAmount:
          type: number
          nullable: true
        proposedCurrencyCode:
          type: string
          nullable: true
        proposedPickupTerms:
          type: string
          nullable: true
        proposedDeliveryTerms:
          type: string
          nullable: true

    ReservationCreateRequest:
      type: object
      required: [listingId, negotiationId, reservedQuantity, reservedUnit]
      properties:
        listingId:
          type: string
          format: uuid
        negotiationId:
          type: string
          format: uuid
        reservedQuantity:
          type: number
          exclusiveMinimum: 0
        reservedUnit:
          $ref: '#/components/schemas/UnitCode'
        expiresAt:
          type: string
          format: date-time
          nullable: true

    ReservationStatusTransitionRequest:
      type: object
      required: [toStatus]
      properties:
        toStatus:
          $ref: '#/components/schemas/ReservationStatus'
        reasonCode:
          type: string
          nullable: true

    LogisticsJobCreateRequest:
      type: object
      required: [listingId, logisticsCompanyId, pickupLocationText]
      properties:
        listingId:
          type: string
          format: uuid
        negotiationId:
          type: string
          format: uuid
          nullable: true
        reservationId:
          type: string
          format: uuid
          nullable: true
        logisticsCompanyId:
          type: string
          format: uuid
        pickupLocationText:
          type: string
        deliveryLocationText:
          type: string
          nullable: true
        scheduledPickupAt:
          type: string
          format: date-time
          nullable: true
        scheduledDeliveryAt:
          type: string
          format: date-time
          nullable: true
        executionNotes:
          type: string
          nullable: true

    LogisticsJobUpdateRequest:
      type: object
      properties:
        status:
          $ref: '#/components/schemas/LogisticsJobStatus'
        pickupLocationText:
          type: string
        deliveryLocationText:
          type: string
          nullable: true
        scheduledPickupAt:
          type: string
          format: date-time
          nullable: true
        scheduledDeliveryAt:
          type: string
          format: date-time
          nullable: true
        executionNotes:
          type: string
          nullable: true

    DocumentCreateRequest:
      type: object
      required: [documentType, storageKey, originalFileName, contentType, fileSizeBytes, uploadedByUserId, accessScope]
      properties:
        documentType:
          $ref: '#/components/schemas/DocumentType'
        storageKey:
          type: string
        originalFileName:
          type: string
        contentType:
          type: string
        fileSizeBytes:
          type: integer
          format: int64
        checksum:
          type: string
          nullable: true
        title:
          type: string
          nullable: true
        description:
          type: string
          nullable: true
        uploadedByUserId:
          type: string
          format: uuid
        accessScope:
          $ref: '#/components/schemas/DocumentAccessScope'

    DocumentUploadIntentRequest:
      type: object
      required: [documentType, originalFileName, contentType, fileSizeBytes, accessScope]
      properties:
        documentType:
          $ref: '#/components/schemas/DocumentType'
        originalFileName:
          type: string
        contentType:
          type: string
        fileSizeBytes:
          type: integer
          format: int64
        accessScope:
          $ref: '#/components/schemas/DocumentAccessScope'

    DocumentUploadIntentResponse:
      type: object
      required: [documentId, storageKey, uploadUrl, expiresAt]
      properties:
        documentId:
          type: string
          format: uuid
        storageKey:
          type: string
        uploadUrl:
          type: string
          format: uri
        expiresAt:
          type: string
          format: date-time

    DocumentUpdateRequest:
      type: object
      properties:
        title:
          type: string
          nullable: true
        description:
          type: string
          nullable: true
        accessScope:
          $ref: '#/components/schemas/DocumentAccessScope'

    DocumentStatusTransitionRequest:
      type: object
      required: [toStatus]
      properties:
        toStatus:
          $ref: '#/components/schemas/DocumentStatus'
        reasonCode:
          type: string
          nullable: true

    DocumentDownloadResponse:
      type: object
      required: [documentId, downloadUrl, expiresAt]
      properties:
        documentId:
          type: string
          format: uuid
        downloadUrl:
          type: string
          format: uri
        expiresAt:
          type: string
          format: date-time

    DocumentLinkCreateRequest:
      type: object
      required: [documentId, relatedEntityType, relatedEntityId, relationType, visibleToCounterparty]
      properties:
        documentId:
          type: string
          format: uuid
        relatedEntityType:
          $ref: '#/components/schemas/RelatedEntityType'
        relatedEntityId:
          type: string
          format: uuid
        relationType:
          $ref: '#/components/schemas/DocumentRelationType'
        visibleToCounterparty:
          type: boolean

    DocumentLinkUpdateRequest:
      type: object
      properties:
        visibleToCounterparty:
          type: boolean
        status:
          $ref: '#/components/schemas/DocumentLinkStatus'

    ComplianceCaseCreateRequest:
      type: object
      required: [caseType, relatedEntityType, relatedEntityId]
      properties:
        caseType:
          $ref: '#/components/schemas/ComplianceCaseType'
        relatedEntityType:
          $ref: '#/components/schemas/RelatedEntityType'
        relatedEntityId:
          type: string
          format: uuid
        assignedToUserId:
          type: string
          format: uuid
          nullable: true
        internalNotes:
          type: string
          nullable: true

    ComplianceCaseUpdateRequest:
      type: object
      properties:
        status:
          $ref: '#/components/schemas/ComplianceCaseStatus'
        assignedToUserId:
          type: string
          format: uuid
          nullable: true
        resolutionCode:
          type: string
          nullable: true
        internalNotes:
          type: string
          nullable: true

    AnalyticsEventCreateRequest:
      type: object
      required: [eventName, eventTimestamp]
      properties:
        eventName:
          type: string
        userId:
          type: string
          format: uuid
          nullable: true
        companyId:
          type: string
          format: uuid
          nullable: true
        relatedEntityType:
          $ref: '#/components/schemas/RelatedEntityType'
          nullable: true
        relatedEntityId:
          type: string
          format: uuid
          nullable: true
        eventTimestamp:
          type: string
          format: date-time
        eventPayload:
          type: object
          additionalProperties: true
          nullable: true

    AdminDashboardResponse:
      type: object
      required: [verificationQueueCount, listingReviewQueueCount, openComplianceCasesCount, publishedListingsCount, openInquiriesCount, activeReservationsCount]
      properties:
        verificationQueueCount:
          type: integer
        listingReviewQueueCount:
          type: integer
        openComplianceCasesCount:
          type: integer
        publishedListingsCount:
          type: integer
        openInquiriesCount:
          type: integer
        activeReservationsCount:
          type: integer

    PaginatedUsersResponse:
      type: object
      required: [items, meta]
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/User'
        meta:
          $ref: '#/components/schemas/PaginationMeta'

    RolesResponse:
      type: object
      required: [items]
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/Role'

    PaginatedUserRoleAssignmentsResponse:
      type: object
      required: [items, meta]
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/UserRoleAssignment'
        meta:
          $ref: '#/components/schemas/PaginationMeta'

    PaginatedCompaniesResponse:
      type: object
      required: [items, meta]
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/Company'
        meta:
          $ref: '#/components/schemas/PaginationMeta'

    PaginatedCompanyMembershipsResponse:
      type: object
      required: [items, meta]
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/CompanyMembership'
        meta:
          $ref: '#/components/schemas/PaginationMeta'

    PaginatedCompanyVerificationReviewsResponse:
      type: object
      required: [items, meta]
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/CompanyVerificationReview'
        meta:
          $ref: '#/components/schemas/PaginationMeta'

    MaterialCategoriesResponse:
      type: object
      required: [items]
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/MaterialCategory'

    MaterialSubtypesResponse:
      type: object
      required: [items]
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/MaterialSubtype'

    PaginatedListingsResponse:
      type: object
      required: [items, meta]
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/Listing'
        meta:
          $ref: '#/components/schemas/PaginationMeta'

    ListingPhotosResponse:
      type: object
      required: [items]
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/ListingPhoto'

    PaginatedListingComplianceReviewsResponse:
      type: object
      required: [items, meta]
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/ListingComplianceReview'
        meta:
          $ref: '#/components/schemas/PaginationMeta'

    PaginatedInquiriesResponse:
      type: object
      required: [items, meta]
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/Inquiry'
        meta:
          $ref: '#/components/schemas/PaginationMeta'

    PaginatedNegotiationsResponse:
      type: object
      required: [items, meta]
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/Negotiation'
        meta:
          $ref: '#/components/schemas/PaginationMeta'

    PaginatedNegotiationMessagesResponse:
      type: object
      required: [items, meta]
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/NegotiationMessage'
        meta:
          $ref: '#/components/schemas/PaginationMeta'

    PaginatedReservationsResponse:
      type: object
      required: [items, meta]
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/Reservation'
        meta:
          $ref: '#/components/schemas/PaginationMeta'

    PaginatedLogisticsJobsResponse:
      type: object
      required: [items, meta]
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/LogisticsJob'
        meta:
          $ref: '#/components/schemas/PaginationMeta'

    PaginatedDocumentsResponse:
      type: object
      required: [items, meta]
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/Document'
        meta:
          $ref: '#/components/schemas/PaginationMeta'

    PaginatedDocumentLinksResponse:
      type: object
      required: [items, meta]
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/DocumentLink'
        meta:
          $ref: '#/components/schemas/PaginationMeta'

    PaginatedComplianceCasesResponse:
      type: object
      required: [items, meta]
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/ComplianceCase'
        meta:
          $ref: '#/components/schemas/PaginationMeta'

    PaginatedNotificationsResponse:
      type: object
      required: [items, meta]
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/Notification'
        meta:
          $ref: '#/components/schemas/PaginationMeta'

    PaginatedAuditEventsResponse:
      type: object
      required: [items, meta]
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/AuditEvent'
        meta:
          $ref: '#/components/schemas/PaginationMeta'

    UserResponse:
      type: object
      required: [data]
      properties:
        data:
          $ref: '#/components/schemas/User'

    UserRoleAssignmentResponse:
      type: object
      required: [data]
      properties:
        data:
          $ref: '#/components/schemas/UserRoleAssignment'

    CompanyResponse:
      type: object
      required: [data]
      properties:
        data:
          $ref: '#/components/schemas/Company'

    CompanyMembershipResponse:
      type: object
      required: [data]
      properties:
        data:
          $ref: '#/components/schemas/CompanyMembership'

    CompanyVerificationReviewResponse:
      type: object
      required: [data]
      properties:
        data:
          $ref: '#/components/schemas/CompanyVerificationReview'

    MaterialCategoryResponse:
      type: object
      required: [data]
      properties:
        data:
          $ref: '#/components/schemas/MaterialCategory'

    MaterialSubtypeResponse:
      type: object
      required: [data]
      properties:
        data:
          $ref: '#/components/schemas/MaterialSubtype'

    ListingResponse:
      type: object
      required: [data]
      properties:
        data:
          $ref: '#/components/schemas/Listing'

    ListingPhotoResponse:
      type: object
      required: [data]
      properties:
        data:
          $ref: '#/components/schemas/ListingPhoto'

    ListingComplianceReviewResponse:
      type: object
      required: [data]
      properties:
        data:
          $ref: '#/components/schemas/ListingComplianceReview'

    InquiryResponse:
      type: object
      required: [data]
      properties:
        data:
          $ref: '#/components/schemas/Inquiry'

    NegotiationResponse:
      type: object
      required: [data]
      properties:
        data:
          $ref: '#/components/schemas/Negotiation'

    NegotiationMessageResponse:
      type: object
      required: [data]
      properties:
        data:
          $ref: '#/components/schemas/NegotiationMessage'

    ReservationResponse:
      type: object
      required: [data]
      properties:
        data:
          $ref: '#/components/schemas/Reservation'

    LogisticsJobResponse:
      type: object
      required: [data]
      properties:
        data:
          $ref: '#/components/schemas/LogisticsJob'

    DocumentResponse:
      type: object
      required: [data]
      properties:
        data:
          $ref: '#/components/schemas/Document'

    DocumentLinkResponse:
      type: object
      required: [data]
      properties:
        data:
          $ref: '#/components/schemas/DocumentLink'

    ComplianceCaseResponse:
      type: object
      required: [data]
      properties:
        data:
          $ref: '#/components/schemas/ComplianceCase'

    NotificationResponse:
      type: object
      required: [data]
      properties:
        data:
          $ref: '#/components/schemas/Notification'

    AnalyticsEventResponse:
      type: object
      required: [data]
      properties:
        data:
          $ref: '#/components/schemas/AnalyticsEvent'
